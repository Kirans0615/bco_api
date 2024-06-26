# Generated by Django 3.2.13 on 2024-04-11 21:16

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('prefix', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Bco',
            fields=[
                ('object_id', models.TextField(primary_key=True, serialize=False)),
                ('contents', models.JSONField()),
                ('state', models.CharField(choices=[('REFERENCED', 'referenced'), ('PUBLISHED', 'published'), ('DRAFT', 'draft'), ('DELETE', 'delete')], default='DRAFT', max_length=20)),
                ('score', models.IntegerField(default=0)),
                ('last_update', models.DateTimeField()),
                ('access_count', models.IntegerField(default=0)),
                ('authorized_users', models.ManyToManyField(blank=True, related_name='authorized_bcos', to=settings.AUTH_USER_MODEL)),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='owned_bcos', to=settings.AUTH_USER_MODEL, to_field='username')),
                ('prefix', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='prefix.prefix')),
            ],
        ),
    ]
