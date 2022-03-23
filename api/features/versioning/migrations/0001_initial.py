# Generated by Django 3.2.12 on 2022-03-23 16:02

from django.db import migrations, models
import django.db.models.deletion
import django_lifecycle.mixins


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('environments', '0017_add_environment_api_key_model'),
        ('features', '0036_remove_existing_constraints'),
    ]

    operations = [
        migrations.CreateModel(
            name='EnvironmentFeatureVersion',
            fields=[
                ('sha', models.CharField(max_length=64, primary_key=True, serialize=False)),
                ('live_from', models.DateTimeField(null=True)),
                ('environment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='environments.environment')),
                ('feature', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='features.feature')),
            ],
            options={
                'abstract': False,
            },
            bases=(django_lifecycle.mixins.LifecycleModelMixin, models.Model),
        ),
        migrations.AddIndex(
            model_name='environmentfeatureversion',
            index=models.Index(fields=['environment', 'feature'], name='versioning__environ_d9d95a_idx'),
        ),
    ]