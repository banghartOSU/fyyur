"""empty message

Revision ID: 7e314802c9a6
Revises: 8d71d5f66e76
Create Date: 2019-12-23 08:49:20.060876

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7e314802c9a6'
down_revision = '8d71d5f66e76'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Artist', sa.Column('website', sa.String(length=500), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Artist', 'website')
    # ### end Alembic commands ###