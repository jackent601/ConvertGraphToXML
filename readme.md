## About

This converts the json output from django's graph_models utility into neat xml in order to edit in draw.io
Inspired from https://github.com/hbmartin/graphviz2drawio/tree/master however with cleaner formatting and links.

It supports different levels of relationship mapping (see below)

XML templating can be editing in this script directly

Once loaded into draw.io recommended to:

- Arrange>Autosize
- Arrange>Layout>[choice]

  as boxes originally created overlapping

## Installation

Simply pull this git repo and run convertGraphModelJsonToDrawIO.py

see usage below for params

## Usage

Required arguments:

```
--graph_models_json PATH    path to the json file output grom 'python manage.py graph_models --json ...'
```

Relational Options, this tool can be ran in multiple mode to create links:

```
--populateAllRelations      This takes the relations fields in json and creates a link from model <-> model
                            Beware, this does not create the cleanest UML as it draws from box to box but captures all relation detail

--attemptFKRelations        This reads the value of each field within a model and if ForeignKey, OneToOne, or MantToMany will link the specific field _within_ the model to the target model based on name. Note: because this is based on field NAME it must match target model NAME, however mappings can be provided in a json file which is an array of {"name": FIELD_NAME, "maps_to": TARGET_MODEL_NAME }

--nameMappingsJsonPath      path for mappings override, see above attemptFKRelations
```

Additional options

```
--omitDjangoModels      Omit any models starting with 'django.'
--output                where to save xml output
```

Once loaded into draw.io recommended to:

- Arrange>Autosize
- Arrange>Layout>[choice]

  as boxes originally created overlapping