# Generated by Django 5.1.1 on 2024-10-01 21:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thrifto', '0002_userprofile_confirm_kyc_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='device',
            name='ip_address',
            field=models.GenericIPAddressField(blank=True, null=True),
        ),
    ]
