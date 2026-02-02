from prepare_migration import generateFile

generateFile(
    git_hub_account='TOKEN',
    from_db='original_v12_zoppellaro',
    from_version=12,
    to_version=18,
    user='odoo',
    data_dir='',
    to_dir='',
    extra_repo=[]
)
