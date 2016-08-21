"""add compressed and ice flag

Revision ID: 40c19270503d
Revises: 479a4b40f818
Create Date: 2016-08-18 14:52:04.085053

"""

# revision identifiers, used by Alembic.
revision = '40c19270503d'
down_revision = '479a4b40f818'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('ore_refining', sa.Column('is_compressed', sa.Boolean(), nullable=True))
    op.add_column('ore_refining', sa.Column('is_ice', sa.Boolean(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ore_refining', 'is_ice')
    op.drop_column('ore_refining', 'is_compressed')
    ### end Alembic commands ###
