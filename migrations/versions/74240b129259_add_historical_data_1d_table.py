from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '74240b129259'
down_revision = 'c4de77626f39'
branch_labels = None
depends_on = None

def upgrade():
    # Step 1: Add the `id` column as nullable
    with op.batch_alter_table('stock_symbols', schema=None) as batch_op:
        batch_op.add_column(sa.Column('id', sa.Integer(), nullable=True))

    # Step 2: Populate `id` with unique values
    op.execute("""
        DO $$
        BEGIN
            -- Create a sequence
            IF NOT EXISTS (SELECT 1 FROM pg_class WHERE relname = 'stock_symbols_id_seq') THEN
                CREATE SEQUENCE stock_symbols_id_seq;
            END IF;

            -- Assign unique values to the 'id' column
            UPDATE stock_symbols
            SET id = nextval('stock_symbols_id_seq');
        END $$;
    """)

    # Step 3: Make `id` column NOT NULL and set it as a primary key
    with op.batch_alter_table('stock_symbols', schema=None) as batch_op:
        batch_op.alter_column('id', nullable=False)
        batch_op.create_primary_key('pk_stock_symbols', ['id'])


def downgrade():
    with op.batch_alter_table('stock_symbols', schema=None) as batch_op:
        batch_op.drop_constraint('pk_stock_symbols', type_='primary')
        batch_op.drop_column('id')
