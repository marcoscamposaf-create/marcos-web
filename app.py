from flask import Flask, jsonify, request, render_template, send_file
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import os
import json
import io
import threading
from models import db, Despesa, Recebimento, Categoria, Cliente, Caixa

app = Flask(__name__)

# ─── Database Configuration
DATABASE_PATH = os.environ.get('DATABASE_PATH', 'marcos.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DATABASE_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

MESES_PT = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
            'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']

FORMAS = ['PIX', 'BOLETO BANCARIO', 'TED', 'DINHEIRO', 'CARTAO']

# ─────────────── Helper Functions ───────────────

def calc_status(venc, liq):
    if str(liq).strip() == 'Sim':
        return 'Pago'
    return 'Atrasado' if venc < date.today() else 'Pendente'


def calc_prio(cat, liq, dias, status):
    if str(liq).strip() == 'Sim':
        return 'Pago'
    if status == 'Atrasado' or cat in ('IMPOSTO', 'FOLHA DE PAGAMENTO'):
        return '1-CRITICO'
    if dias <= 7 or cat in ('ABASTECIMENTO', 'LUZ E AGUA'):
        return '2-ALTO'
    if dias <= 30:
        return '3-MEDIO'
    return '4-BAIXO'


def update_despesa_calc(desp):
    """Atualizar campos calculados de uma despesa"""
    desp.dias = (desp.vencimento - date.today()).days
    desp.status = calc_status(desp.vencimento, desp.liquidado)
    desp.prioridade = calc_prio(desp.categoria, desp.liquidado, desp.dias, desp.status)


def update_recebimento_status(recb):
    """Atualizar status de um recebimento"""
    if recb.valor_recebido >= recb.valor_esperado and recb.valor_esperado > 0:
        recb.status = 'Recebido'
    elif recb.vencimento < date.today():
        recb.status = 'Atrasado'
    else:
        recb.status = 'A Receber'


def build_dashboard_data():
    """Construir dados do dashboard"""
    desp = Despesa.query.all()
    recb = Recebimento.query.all()
    caixa_obj = Caixa.query.first()
    caixa = caixa_obj.saldo if caixa_obj else 0.0

    pend = [d for d in desp if d.liquidado != 'Sim']
    tp = sum(d.valor_previsto for d in pend)
    tr = sum(r.valor_esperado for r in recb)
    trec = sum(r.valor_recebido for r in recb)
    ta_receber = sum(r.valor_esperado for r in recb if r.status != 'Recebido')
    tpago = sum(d.valor_pago for d in desp if d.liquidado == 'Sim')
    tg = sum(d.valor_previsto for d in desp)
    taxa = round(tpago / tg * 100, 1) if tg > 0 else 0
    venc = sum(d.valor_previsto for d in pend if d.dias < 0)
    media = tg / 7
    meses = round(caixa / media, 2) if media > 0 else 0
    saldo_liquido = caixa + ta_receber - tp

    por_prio = {}
    for d in pend:
        p = d.prioridade
        por_prio.setdefault(p, {'valor': 0, 'qtd': 0})
        por_prio[p]['valor'] += d.valor_previsto
        por_prio[p]['qtd'] += 1

    por_cat = {}
    for d in desp:
        por_cat[d.categoria] = por_cat.get(d.categoria, 0) + d.valor_previsto
    top_cats = sorted(por_cat.items(), key=lambda x: x[1], reverse=True)[:6]

    por_mes = {}
    for d in desp:
        m = d.vencimento.strftime('%Y-%m')
        por_mes.setdefault(m, {'pago': 0, 'pendente': 0, 'total': 0})
        if d.liquidado == 'Sim':
            por_mes[m]['pago'] += d.valor_previsto
        else:
            por_mes[m]['pendente'] += d.valor_previsto
        por_mes[m]['total'] += d.valor_previsto

    por_mes_recb = {}
    for r in recb:
        m = r.vencimento.strftime('%Y-%m')
        por_mes_recb.setdefault(m, {'esperado': 0, 'recebido': 0})
        por_mes_recb[m]['esperado'] += r.valor_esperado
        por_mes_recb[m]['recebido'] += r.valor_recebido

    urgentes = sorted([d for d in pend if d.dias <= 7], key=lambda x: x['dias'])[:8]
    urgentes = [d.to_dict() for d in urgentes]

    return {
        'caixa': caixa,
        'total_pagar': tp,
        'total_receber': tr,
        'total_recebido': trec,
        'ta_receber': ta_receber,
        'vencidas': venc,
        'meses_caixa': meses,
        'taxa_liquidacao': taxa,
        'total_pendentes': len(pend),
        'saldo_liquido': saldo_liquido,
        'por_prioridade': por_prio,
        'top_categorias': [{'cat': c, 'valor': v} for c, v in top_cats],
        'por_mes': {k: v for k, v in sorted(por_mes.items())},
        'por_mes_recb': {k: v for k, v in sorted(por_mes_recb.items())},
        'urgentes': urgentes,
    }


# ─────────────── PDF Report ───────────────

def gerar_pdf_relatorio(tipo='completo', mes_filtro=None):
    """Gerar relatório PDF"""
    try:
        buf = io.BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4), topMargin=0.5*cm, bottomMargin=0.5*cm)
        story = []
        
        # Título
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=18,
            textColor=colors.HexColor('#2f5d50'),
            spaceAfter=12,
            alignment=TA_CENTER,
        )
        story.append(Paragraph('RELATÓRIO FINANCEIRO - MARCOS', title_style))
        story.append(Paragraph(f'Gerado em {date.today().strftime("%d/%m/%Y")}', styles['Normal']))
        story.append(Spacer(1, 0.5*cm))
        
        # Dashboard (tipo completo)
        if tipo in ('completo',):
            story.append(Paragraph('RESUMO EXECUTIVO', styles['Heading2']))
            data = build_dashboard_data()
            kpi_data = [
                ['CAIXA', f"R$ {data['caixa']:,.2f}"],
                ['A PAGAR', f"R$ {data['total_pagar']:,.2f}"],
                ['A RECEBER', f"R$ {data['ta_receber']:,.2f}"],
                ['SALDO LÍQUIDO', f"R$ {data['saldo_liquido']:,.2f}"],
                ['TAXA LIQUIDAÇÃO', f"{data['taxa_liquidacao']:.1f}%"],
            ]
            kpi_table = Table(kpi_data, colWidths=[3*cm, 5*cm])
            kpi_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.grey),
            ]))
            story.append(kpi_table)
            story.append(Spacer(1, 0.5*cm))
        
        # Despesas
        if tipo in ('completo', 'despesas'):
            story.append(Paragraph('CONTAS A PAGAR', styles['Heading2']))
            desp = Despesa.query.all()
            if mes_filtro:
                desp = [d for d in desp if d.vencimento.strftime('%Y-%m') == mes_filtro]
            
            if desp:
                desp_data = [['Vencimento', 'Fornecedor', 'Categoria', 'Descrição', 'Valor', 'Status', 'Prioridade']]
                for d in desp:
                    desp_data.append([
                        d.vencimento.strftime('%d/%m/%Y'),
                        d.fornecedor[:20],
                        d.categoria[:15],
                        d.descricao[:20],
                        f"R$ {d.valor_previsto:,.2f}",
                        d.status,
                        d.prioridade,
                    ])
                
                desp_table = Table(desp_data, colWidths=[1.5*cm, 2.5*cm, 2*cm, 2.5*cm, 1.8*cm, 1.5*cm, 1.8*cm])
                desp_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2f5d50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                story.append(desp_table)
            else:
                story.append(Paragraph('Nenhuma despesa encontrada.', styles['Normal']))
            
            story.append(PageBreak())
        
        # Recebimentos
        if tipo in ('completo', 'receitas'):
            story.append(Paragraph('CONTAS A RECEBER', styles['Heading2']))
            recb = Recebimento.query.all()
            if mes_filtro:
                recb = [r for r in recb if r.vencimento.strftime('%Y-%m') == mes_filtro]
            
            if recb:
                recb_data = [['Vencimento', 'Cliente', 'Descrição', 'Valor Esperado', 'Valor Recebido', 'Status']]
                for r in recb:
                    recb_data.append([
                        r.vencimento.strftime('%d/%m/%Y'),
                        r.cliente[:25],
                        r.descricao[:30],
                        f"R$ {r.valor_esperado:,.2f}",
                        f"R$ {r.valor_recebido:,.2f}",
                        r.status,
                    ])
                
                recb_table = Table(recb_data, colWidths=[1.8*cm, 3*cm, 3*cm, 2.2*cm, 2.2*cm, 2*cm])
                recb_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2f5d50')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ]))
                story.append(recb_table)
            else:
                story.append(Paragraph('Nenhum recebimento encontrado.', styles['Normal']))
        
        doc.build(story)
        buf.seek(0)
        return buf, None
    except Exception as e:
        return None, str(e)


# ─────────────── Routes ───────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/dashboard')
def api_dashboard():
    data = build_dashboard_data()
    return jsonify(data)


@app.route('/api/despesas', methods=['GET'])
def api_get_despesas():
    desp = Despesa.query.all()
    desp.sort(key=lambda x: x.dias)
    return jsonify([d.to_dict() for d in desp])


@app.route('/api/despesas', methods=['POST'])
def api_add_despesa():
    data = request.json
    venc = datetime.strptime(data['vencimento'], '%Y-%m-%d').date()
    liq = data.get('liquidado', 'Não')
    cat = data.get('categoria', '')
    
    desp = Despesa(
        vencimento=venc,
        mes=MESES_PT[venc.month - 1],
        fornecedor=data.get('fornecedor', ''),
        categoria=cat,
        descricao=data.get('descricao', ''),
        forma_pgto=data.get('forma_pgto', ''),
        valor_previsto=float(data.get('valor_previsto', 0)),
        valor_pago=float(data.get('valor_pago', 0)),
        liquidado=liq,
    )
    
    update_despesa_calc(desp)
    db.session.add(desp)
    db.session.commit()
    
    return jsonify({'ok': True, 'id': desp.id})


@app.route('/api/despesas/<int:desp_id>', methods=['PUT'])
def api_update_despesa(desp_id):
    desp = Despesa.query.get(desp_id)
    if not desp:
        return jsonify({'ok': False, 'erro': 'Despesa não encontrada'}), 404
    
    data = request.json
    if 'vencimento' in data:
        desp.vencimento = datetime.strptime(data['vencimento'], '%Y-%m-%d').date()
    if 'fornecedor' in data:
        desp.fornecedor = data['fornecedor']
    if 'categoria' in data:
        desp.categoria = data['categoria']
    if 'descricao' in data:
        desp.descricao = data['descricao']
    if 'forma_pgto' in data:
        desp.forma_pgto = data['forma_pgto']
    if 'valor_previsto' in data:
        desp.valor_previsto = float(data['valor_previsto'])
    if 'valor_pago' in data:
        desp.valor_pago = float(data['valor_pago'])
    if 'liquidado' in data:
        desp.liquidado = data['liquidado']
    
    update_despesa_calc(desp)
    db.session.commit()
    
    return jsonify({'ok': True})


@app.route('/api/despesas/<int:desp_id>', methods=['DELETE'])
def api_delete_despesa(desp_id):
    desp = Despesa.query.get(desp_id)
    if not desp:
        return jsonify({'ok': False, 'erro': 'Despesa não encontrada'}), 404
    
    db.session.delete(desp)
    db.session.commit()
    
    return jsonify({'ok': True})


@app.route('/api/recebimentos', methods=['GET'])
def api_get_recebimentos():
    recb = Recebimento.query.all()
    return jsonify([r.to_dict() for r in recb])


@app.route('/api/recebimentos', methods=['POST'])
def api_add_recebimento():
    data = request.json
    venc = datetime.strptime(data['vencimento'], '%Y-%m-%d').date()
    
    recb = Recebimento(
        vencimento=venc,
        cliente=data.get('cliente', ''),
        descricao=data.get('descricao', ''),
        valor_esperado=float(data.get('valor_esperado', 0)),
        valor_recebido=float(data.get('valor_recebido', 0)),
    )
    
    update_recebimento_status(recb)
    db.session.add(recb)
    db.session.commit()
    
    return jsonify({'ok': True, 'id': recb.id})


@app.route('/api/recebimentos/<int:recb_id>', methods=['PUT'])
def api_update_recebimento(recb_id):
    recb = Recebimento.query.get(recb_id)
    if not recb:
        return jsonify({'ok': False, 'erro': 'Recebimento não encontrado'}), 404
    
    data = request.json
    if 'vencimento' in data:
        recb.vencimento = datetime.strptime(data['vencimento'], '%Y-%m-%d').date()
    if 'cliente' in data:
        recb.cliente = data['cliente']
    if 'descricao' in data:
        recb.descricao = data['descricao']
    if 'valor_esperado' in data:
        recb.valor_esperado = float(data['valor_esperado'])
    if 'valor_recebido' in data:
        recb.valor_recebido = float(data['valor_recebido'])
    
    update_recebimento_status(recb)
    db.session.commit()
    
    return jsonify({'ok': True})


@app.route('/api/recebimentos/<int:recb_id>', methods=['DELETE'])
def api_delete_recebimento(recb_id):
    recb = Recebimento.query.get(recb_id)
    if not recb:
        return jsonify({'ok': False, 'erro': 'Recebimento não encontrado'}), 404
    
    db.session.delete(recb)
    db.session.commit()
    
    return jsonify({'ok': True})


@app.route('/api/caixa', methods=['GET'])
def api_get_caixa():
    caixa = Caixa.query.first()
    if not caixa:
        caixa = Caixa(id=1, saldo=0.0)
        db.session.add(caixa)
        db.session.commit()
    return jsonify({'saldo': caixa.saldo})


@app.route('/api/caixa', methods=['PUT'])
def api_update_caixa():
    caixa = Caixa.query.first()
    if not caixa:
        caixa = Caixa(id=1, saldo=0.0)
        db.session.add(caixa)
    
    caixa.saldo = float(request.json['valor'])
    db.session.commit()
    
    return jsonify({'ok': True})


@app.route('/api/categorias/pagar', methods=['GET'])
def api_get_cats_pagar():
    cats = Categoria.query.filter_by(tipo='pagar').all()
    return jsonify([c.nome for c in cats])


@app.route('/api/categorias/pagar', methods=['POST'])
def api_add_cat_pagar():
    nome = request.json.get('nome', '').upper()
    if not nome:
        return jsonify({'ok': False, 'erro': 'Nome vazio'}), 400
    
    existing = Categoria.query.filter_by(tipo='pagar', nome=nome).first()
    if existing:
        return jsonify({'ok': False, 'erro': 'Já existe'}), 400
    
    cat = Categoria(tipo='pagar', nome=nome)
    db.session.add(cat)
    db.session.commit()
    
    return jsonify({'ok': True, 'categorias': [c.nome for c in Categoria.query.filter_by(tipo='pagar').all()]})


@app.route('/api/categorias/pagar/<path:nome>', methods=['DELETE'])
def api_del_cat_pagar(nome):
    cat = Categoria.query.filter_by(tipo='pagar', nome=nome.upper()).first()
    if not cat:
        return jsonify({'ok': False, 'erro': 'Não encontrado'}), 404
    
    db.session.delete(cat)
    db.session.commit()
    
    return jsonify({'ok': True, 'categorias': [c.nome for c in Categoria.query.filter_by(tipo='pagar').all()]})


@app.route('/api/categorias/receber', methods=['GET'])
def api_get_cats_receber():
    cats = Categoria.query.filter_by(tipo='receber').all()
    return jsonify([c.nome for c in cats])


@app.route('/api/categorias/receber', methods=['POST'])
def api_add_cat_receber():
    nome = request.json.get('nome', '').upper()
    if not nome:
        return jsonify({'ok': False, 'erro': 'Nome vazio'}), 400
    
    existing = Categoria.query.filter_by(tipo='receber', nome=nome).first()
    if existing:
        return jsonify({'ok': False, 'erro': 'Já existe'}), 400
    
    cat = Categoria(tipo='receber', nome=nome)
    db.session.add(cat)
    db.session.commit()
    
    return jsonify({'ok': True, 'categorias': [c.nome for c in Categoria.query.filter_by(tipo='receber').all()]})


@app.route('/api/categorias/receber/<path:nome>', methods=['DELETE'])
def api_del_cat_receber(nome):
    cat = Categoria.query.filter_by(tipo='receber', nome=nome.upper()).first()
    if not cat:
        return jsonify({'ok': False, 'erro': 'Não encontrado'}), 404
    
    db.session.delete(cat)
    db.session.commit()
    
    return jsonify({'ok': True, 'categorias': [c.nome for c in Categoria.query.filter_by(tipo='receber').all()]})


@app.route('/api/clientes', methods=['GET'])
def api_get_clientes():
    clientes = Cliente.query.all()
    return jsonify([c.nome for c in clientes])


@app.route('/api/clientes', methods=['POST'])
def api_add_cliente():
    nome = request.json.get('nome', '').upper()
    if not nome:
        return jsonify({'ok': False, 'erro': 'Nome vazio'}), 400
    
    existing = Cliente.query.filter_by(nome=nome).first()
    if existing:
        return jsonify({'ok': False, 'erro': 'Já existe'}), 400
    
    cliente = Cliente(nome=nome)
    db.session.add(cliente)
    db.session.commit()
    
    return jsonify({'ok': True, 'clientes': [c.nome for c in Cliente.query.all()]})


@app.route('/api/clientes/<path:nome>', methods=['DELETE'])
def api_del_cliente(nome):
    cliente = Cliente.query.filter_by(nome=nome.upper()).first()
    if not cliente:
        return jsonify({'ok': False, 'erro': 'Não encontrado'}), 404
    
    db.session.delete(cliente)
    db.session.commit()
    
    return jsonify({'ok': True, 'clientes': [c.nome for c in Cliente.query.all()]})


@app.route('/api/relatorio/pdf')
def api_relatorio_pdf():
    tipo = request.args.get('tipo', 'completo')
    mes = request.args.get('mes', None)
    buf, erro = gerar_pdf_relatorio(tipo=tipo, mes_filtro=mes)
    
    if erro:
        return jsonify({'ok': False, 'erro': erro}), 500
    
    nome = f"relatorio_marcos_{date.today().strftime('%Y%m%d')}.pdf"
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=True, download_name=nome)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print(f'\n  Marcos Web (Database) — http://localhost:5000')
        print(f'  Database: {os.path.abspath(DATABASE_PATH)}\n')
    
    app.run(debug=False, port=5000)
