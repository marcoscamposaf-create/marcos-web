from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date

db = SQLAlchemy()

class Categoria(db.Model):
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    tipo = db.Column(db.String(50), nullable=False)  # 'pagar', 'receber', 'cliente'
    nome = db.Column(db.String(255), nullable=False, unique=True)
    descricao = db.Column(db.Text)
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'tipo': self.tipo,
            'nome': self.nome,
            'descricao': self.descricao,
        }


class Cliente(db.Model):
    __tablename__ = 'clientes'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False, unique=True)
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    
    recebimentos = db.relationship('Recebimento', backref='cliente_obj', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'nome': self.nome,
        }


class Despesa(db.Model):
    __tablename__ = 'despesas'
    
    id = db.Column(db.Integer, primary_key=True)
    vencimento = db.Column(db.Date, nullable=False)
    mes = db.Column(db.String(20))
    fornecedor = db.Column(db.String(255))
    categoria = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text)
    forma_pgto = db.Column(db.String(50))
    valor_previsto = db.Column(db.Float, default=0.0)
    valor_pago = db.Column(db.Float, default=0.0)
    liquidado = db.Column(db.String(10), default='Não')  # 'Sim' ou 'Não'
    status = db.Column(db.String(20))  # 'Pendente', 'Pago', 'Atrasado'
    dias = db.Column(db.Integer)
    prioridade = db.Column(db.String(20))  # '1-CRITICO', '2-ALTO', '3-MEDIO', '4-BAIXO', 'Pago'
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    data_update = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'vencimento': self.vencimento.strftime('%Y-%m-%d'),
            'mes': self.mes,
            'fornecedor': self.fornecedor,
            'categoria': self.categoria,
            'descricao': self.descricao,
            'forma_pgto': self.forma_pgto,
            'valor_previsto': self.valor_previsto,
            'valor_pago': self.valor_pago,
            'liquidado': self.liquidado,
            'status': self.status,
            'dias': self.dias,
            'prioridade': self.prioridade,
        }


class Recebimento(db.Model):
    __tablename__ = 'recebimentos'
    
    id = db.Column(db.Integer, primary_key=True)
    vencimento = db.Column(db.Date, nullable=False)
    cliente_id = db.Column(db.Integer, db.ForeignKey('clientes.id'), nullable=True)
    cliente = db.Column(db.String(255))  # para compatibilidade
    descricao = db.Column(db.Text)
    valor_esperado = db.Column(db.Float, default=0.0)
    valor_recebido = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20))  # 'A Receber', 'Recebido', 'Atrasado'
    data_criacao = db.Column(db.DateTime, default=datetime.now)
    data_update = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'id': self.id,
            'vencimento': self.vencimento.strftime('%Y-%m-%d'),
            'cliente': self.cliente or (self.cliente_obj.nome if self.cliente_obj else ''),
            'descricao': self.descricao,
            'valor_esperado': self.valor_esperado,
            'valor_recebido': self.valor_recebido,
            'status': self.status,
        }


class Caixa(db.Model):
    __tablename__ = 'caixa'
    
    id = db.Column(db.Integer, primary_key=True, default=1)
    saldo = db.Column(db.Float, default=0.0)
    data_update = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    
    def to_dict(self):
        return {
            'saldo': self.saldo,
            'data_update': self.data_update.isoformat(),
        }
