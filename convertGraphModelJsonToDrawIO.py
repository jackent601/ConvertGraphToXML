import json
import string
import random
import argparse

# for unique ids in drawio xml
def id_generator(size=6, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

USAGE_DOC="""
    This converts the json output from django's graph_models utility into neat xml in order to edit in draw.io
    Inspired from https://github.com/hbmartin/graphviz2drawio/tree/master however with cleaner formatting and links.

    XML templating can be editing in this script directly

    Required arguments:
        --graph_models_json PATH    path to the json file output grom 'python manage.py graph_models --json ...'

    Relational Options, this tool can be ran in multiple mode to create links:

        --populateAllRelations      This takes the relations fields in json and creates a link from model <-> model
                                    Beware, this does not create the cleanest UML as it draws from box to box but captures
                                    all relation detail

        --attemptFKRelations        This reads the value of each field within a model and if ForeignKey, OneToOne, or MantToMany 
                                    will link the specific field _within_ the model to the target model based on name.
                                    Note: because this is based on field NAME it must match target model NAME, however mappings
                                    can be provided in a json file which is an array of {"name": FIELD_NAME, "maps_to": TARGET_MODEL_NAME }
        --nameMappingsJsonPath      path for mappings override, see above attemptFKRelations

    Additional options
        --omitDjangoModels          Omit any models starting with 'django.'


    Once loaded into draw.io recommended to:
        Arrange>Autosize
        Arrange>Layout>[choice]
    as boxes originally created overlapping
"""

# Paths to field names from graph_models json output
# path to graph components from master json
GRAPH_PATH = 'graphs'
# paths within each graph(app) component
APP_NAME_PATH='app_name'
MODELS_PATH = 'models'
# paths within each model
MODEL_NAME_PATH='name'
MODEL_FIELDS_PATH='fields'
RELATIONS_PATH = 'relations'
# paths within each field
MODEL_FIELD_NAME_PATH='name'
MODEL_FIELD_TYPE_PATH='type'

XML_DRAWIO_HEADER="""<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="2024-03-23T15:14:09.070Z" agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36" etag="qfASGYTtEwGyzwn4VCDH" version="24.0.9" type="device">
  <diagram name="Page-1" id="751wOO_BoKR00D7IZ9_7">
    <mxGraphModel dx="1050" dy="652" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />"""
XML_DRAWIO_FOOTER="""
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""

def getLineElement(id, src, trgt):
    return f"""
        <mxCell id="{id}" style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;" edge="1" parent="1" source="{src}" target="{trgt}">
          <mxGeometry relative="1" as="geometry" />
        </mxCell>"""

def getClassParent(id, name, x=560, y=290):
    return f"""
        <mxCell id="{id}" value="{name}" style="swimlane;fontStyle=1;align=center;verticalAlign=top;childLayout=stackLayout;horizontal=1;startSize=26;horizontalStack=0;resizeParent=1;resizeParentMax=0;resizeLast=0;collapsible=1;marginBottom=0;whiteSpace=wrap;html=1;" vertex="1" parent="1">
            <mxGeometry x="{x}" y="{y}" width="160" height="86" as="geometry" />
        </mxCell>"""

def getClassChild(parentId, id, value):
    return f"""
        <mxCell id="{id}" value="{value}" style="text;strokeColor=none;fillColor=none;align=left;verticalAlign=top;spacingLeft=4;spacingRight=4;overflow=hidden;rotatable=0;points=[[0,0.5],[1,0.5]];portConstraint=eastwest;whiteSpace=wrap;html=1;" vertex="1" parent="{parentId}">
            <mxGeometry y="26" width="160" height="26" as="geometry" />
        </mxCell>"""


class UMLDrawIOMaster():
    def __init__(self, 
                 jsonpath,
                 omitDjangoModels=False, 
                 populateAllRelations=False, 
                 attemptFKRelations=True,
                 nameMappingsJsonPath=None):
        
        # load json schema
        self.jsonpath =jsonpath
        self.omitDjangoModels = omitDjangoModels
        self.populateAllRelations = populateAllRelations
        self.attemptFKRelations = attemptFKRelations
        with open(jsonpath) as f:
            jsonMaster = json.load(f)
            
        # Extract each graph element into an 'app' class
        apps = []
        for app in jsonMaster[GRAPH_PATH]:
            if omitDjangoModels and app[APP_NAME_PATH].startswith('django.'):
                continue
            apps.append(UMLDrawIOApp(app))
        self.apps = apps

        # load name maps
        if nameMappingsJsonPath is not None:
            with open(nameMappingsJsonPath) as m:
                mappings = json.load(m)
            self.mappings = mappings
        else:
            self.mappings = None

    def getXML(self):
        # header
        res = f"{XML_DRAWIO_HEADER}"
        
        # create class boxes
        for a in self.apps:
            aXML = a.getAppXML()
            res += f"{aXML}"
        
        # create links 
        if self.populateAllRelations:
            for a in self.apps:
                for m in a.models:
                    for r in m.relations:
                        target = r['target']
                        targetModel = self.getTargetModel(target)
                        if targetModel is not None:
                            lineElem = getLineElement(f"{m.name}_lineTo_{targetModel.name}", m.parent_id, targetModel.parent_id)
                            res += f"{lineElem}"
        
        elif self.attemptFKRelations:
            for a in self.apps:
                for m in a.models:
                    for f in m.fields:
                        if "FOREIGNKEY" in f.type.upper() or "MANYTOMANY" in f.type.upper() or "ONETOONEFIELD" in f.type.upper():
                            targetModel = self.getTargetModel(f.name)
                            if targetModel is None:
                                print(f"couldnt find FK for: {f.name}")
                            else:
                                rand = id_generator()
                                lineElem = getLineElement(f"{f.name}_lineTo_{targetModel.name}_{rand}", f.fieldid, targetModel.parent_id)
                                res += f"{lineElem}"   
        # footer
        res += f"{XML_DRAWIO_FOOTER}"
        self.XML = res
        return res
    
    def getTargetModel(self, target):
        target = target.lower()

        # handle some naming conventions
        if self.mappings is not None:
            for map in self.mappings:
                if target == map['name'].lower():
                    target = map['maps_to'].lower()

        for _a in self.apps:
            for _m in _a.models:
                if _m.name.lower() == target:
                    return _m
        return None
    
    def writeXML(self, output):
        with open(output, "w") as out:
            out.write(self.XML)

    def __str__(self):
        result = ""
        for a in self.apps:
            result += f'{a.app_name}\n'
            for m in a.models:
                result += f'\t{m.name}\n'
        return result

class UMLDrawIOApp():
    def __init__(self, appJson):
        self.app_name=appJson[APP_NAME_PATH]

        # extract each model
        models=[]
        for m in appJson[MODELS_PATH]:
            models.append(UMLDrawIOModel(m))
        self.models=models

    def getAppXML(self):
        res=""
        for m in self.models:
            modelXML = m.getModelXML()
            res += f'{modelXML}'
        return res


class UMLDrawIOModel():
    def __init__(self, modelJson):
        self.name=modelJson[MODEL_NAME_PATH]
        self.relations=modelJson[RELATIONS_PATH]
        # self.fieldsJson=modelJson[MODEL_FIELDS_PATH]

        # ensure no duplicate ids for similarly named models
        self.id_append=id_generator()
        self.parent_id=f"{self.name}_{self.id_append}_id_1"

        # Add fields
        fields=[]
        field_id = 1
        for f in modelJson[MODEL_FIELDS_PATH]:
            fields.append(UMLDrawIOModelField(f, f'{self.parent_id}_sub_{field_id}'))
            field_id += 1
        self.fields = fields
    
    def getModelXML(self):
        res = ""
        # parentId = f"{self.name}_id_1"
        res += getClassParent(self.parent_id, self.name)
        field_id = 1
        for f in self.fields:
            # fieldXML = self.getClassFieldXML(f, self.parent_id, f.fieldid)
            fieldXML = f.getFieldXML(self.parent_id)
            res += f'{fieldXML}\n'
            field_id += 1
        return res

# needthis to keep track of ids to drwa line conections
class UMLDrawIOModelField():
    def __init__(self, jsonField, id):
        self.name = jsonField[MODEL_FIELD_NAME_PATH]
        self.type = jsonField[MODEL_FIELD_TYPE_PATH]
        self.fieldid = id

    def getFieldXML(self, parentId):
        fieldString = f'{self.name}: {self.type}'
        return getClassChild(parentId, self.fieldid, fieldString)


if __name__ == '__main__':
    USAGE_HELP="""
        This converts the json output from django's graph_models utility into neat xml in order to edit in draw.io
    Inspired from https://github.com/hbmartin/graphviz2drawio/tree/master however with cleaner formatting and links.

    XML templating can be editing in this script directly

    Multiple methods for relationship drawing (see options)

    Once loaded into draw.io recommended to:
        Arrange>Autosize
        Arrange>Layout>[choice]
    as boxes originally created overlapping
    """


    populateAllRelationsUsage="""This takes the relations fields in json and creates a link from model <-> model
        Beware, this does not create the cleanest UML as it draws from box to box but captures
        all relation detail

    """
    attemptFKRelationsUsage="""This reads the value of each field within a model and if ForeignKey, OneToOne, or MantToMany 
        will link the specific field _within_ the model to the target model based on name.
        Note: because this is based on field NAME it must match target model NAME, however mappings
        can be provided in a json file which is an array of {"name": FIELD_NAME, "maps_to": TARGET_MODEL_NAME }

    """

    parser = argparse.ArgumentParser(description=USAGE_HELP)
    parser.add_argument(
        '-i', '--graph_models_json', required=True, type=str, help="path to the json file output grom 'python manage.py graph_models --json ...'\n")
    parser.add_argument(
        "-a", "--populateAllRelations", help=populateAllRelationsUsage, action='store_true' )
    parser.add_argument(
        "-r", "--attemptFKRelationsUsage", help=attemptFKRelationsUsage, action='store_true' )
    parser.add_argument(
        '-m', '--nameMappingsJsonPath', required=False, type=str, help="path for mappings override, see --attemptFKRelations\n", default=None)
    parser.add_argument(
        "-d", "--omitDjangoModels", help="Omit any models starting with 'django.'\n", action='store_true' )
    parser.add_argument(
        '-o', '--output', required=False, type=str, help="path to the output xml, if not specified prints to terminal\n", default=None)
    args = parser.parse_args()

    master = UMLDrawIOMaster(args.graph_models_json, 
                             omitDjangoModels=args.omitDjangoModels, 
                             populateAllRelations=args.populateAllRelations,
                             attemptFKRelations=args.attemptFKRelationsUsage,
                             nameMappingsJsonPath=args.nameMappingsJsonPath)
    
    print("loaded json, with following models")
    print(master)

    xml = master.getXML()
    print("parsed into xml")

    if args.output is not None:
        master.writeXML(args.output)
        print(f"wrote xml to: {args.output}")
    else:
        print(xml)

    