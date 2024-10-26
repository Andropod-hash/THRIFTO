# Generated by Django 5.1.2 on 2024-10-23 17:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('thrifto', '0002_alter_wallet_encrypted_balance'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='passwordreset',
            name='test_email_content',
        ),
        migrations.AlterField(
            model_name='passwordreset',
            name='reset_code',
            field=models.CharField(max_length=64, unique=True),
        ),
        migrations.AlterField(
            model_name='wallet',
            name='encrypted_balance',
            field=models.BinaryField(default=b'gAAAAABnGS-hqBsPKxc4ZFNbN8YwH-achmpBna0-IQZZuJ-vZBnHsvkJYfEgsxdSkIoxHAfOgrPYdqk1UOPvpDyX7OwEGEKyFA=='),
        ),
    ]
