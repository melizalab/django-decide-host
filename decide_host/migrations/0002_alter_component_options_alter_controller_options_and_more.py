# Generated by Django 4.2.7 on 2023-11-30 20:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('decide_host', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='component',
            options={'ordering': ('name',)},
        ),
        migrations.AlterModelOptions(
            name='controller',
            options={'ordering': ('name',)},
        ),
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ('-time',)},
        ),
        migrations.AlterModelOptions(
            name='subject',
            options={'ordering': ('name',)},
        ),
        migrations.AlterModelOptions(
            name='trial',
            options={'ordering': ('-time',)},
        ),
        migrations.AlterUniqueTogether(
            name='trial',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='component',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='component',
            name='name',
            field=models.SlugField(max_length=32, unique=True),
        ),
        migrations.AlterField(
            model_name='controller',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='controller',
            name='name',
            field=models.SlugField(max_length=32, unique=True),
        ),
        migrations.AlterField(
            model_name='event',
            name='data',
            field=models.JSONField(),
        ),
        migrations.AlterField(
            model_name='event',
            name='time',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterField(
            model_name='subject',
            name='id',
            field=models.AutoField(primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name='subject',
            name='name',
            field=models.SlugField(max_length=36, unique=True),
        ),
        migrations.AlterField(
            model_name='trial',
            name='data',
            field=models.JSONField(),
        ),
        migrations.AlterField(
            model_name='trial',
            name='time',
            field=models.DateTimeField(db_index=True),
        ),
        migrations.AlterUniqueTogether(
            name='trial',
            unique_together={('name', 'subject', 'time')},
        ),
        migrations.AddIndex(
            model_name='event',
            index=models.Index(fields=['addr', '-time'], name='addr_time_desc_idx'),
        ),
        migrations.AddIndex(
            model_name='trial',
            index=models.Index(fields=['subject', '-time'], name='subject_time_desc_idx'),
        ),
    ]
