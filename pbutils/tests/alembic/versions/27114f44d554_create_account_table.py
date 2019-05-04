"""create_account_table

Revision ID: 27114f44d554
Revises: 
Create Date: 2019-05-03 19:52:58.507439

"""
from alembic import op
import sqlalchemy as sa

from pbutils.mysql_utils import pw_encrypt

# revision identifiers, used by Alembic.
revision = '27114f44d554'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    account_table = op.create_table(
        'account',
        sa.Column('username', sa.String, primary_key=True),
        sa.Column('email', sa.String, unique=True, nullable=False),
        sa.Column('password', sa.String, nullable=False),
        sa.Column('fname', sa.String, nullable=False),
        sa.Column('lname', sa.String, nullable=False),
    )

    op.bulk_insert(account_table,
                   [
                       {'username': 'phonybone', 'email': 'vmc.swdev@gmail.com', 'password': pw_encrypt('fart'.encode()), 'fname': 'Victor', 'lname': 'Cassen'},
                       {'username': 'fred', 'email': 'fred@mailinator.com', 'password': pw_encrypt('fartfred'.encode()), 'fname': 'Fred', 'lname': 'Flintstone'},
                       {'username': 'wilma', 'email': 'wilma@mailinator.com', 'password': pw_encrypt('fartwilma'.encode()), 'fname': 'Wilma', 'lname': 'Flintstone'},
                   ],
                   multiinsert=False
                   )


def downgrade():
    op.drop_table('account')
