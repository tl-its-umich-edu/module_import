from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('module_import', '0001_mysql_cache'),  # Ensure this is the correct dependency
    ]

    operations = [
        migrations.RunSQL(
            sql="DROP TABLE IF EXISTS django_module_import_cache;",
        ),
    ]
