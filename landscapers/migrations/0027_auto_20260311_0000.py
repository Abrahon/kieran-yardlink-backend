from django.db import migrations

def populate_landscaper(apps, schema_editor):
    ClientCustomService = apps.get_model('landscapers', 'ClientCustomService')
    BusinessProfile = apps.get_model('landscapers', 'BusinessProfile')

    default_business = BusinessProfile.objects.first()
    if not default_business:
        return

    ClientCustomService.objects.filter(landscaper__isnull=True).update(
        landscaper=default_business
    )

class Migration(migrations.Migration):

    dependencies = [
        ('landscapers', '0026_alter_addon_options_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_landscaper, migrations.RunPython.noop),
    ]