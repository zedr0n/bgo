import adsk.core
import os

import adsk.fusion
from ...lib import fusion360utils as futil
from ... import config
app = adsk.core.Application.get()
ui = app.userInterface

from ...Divider import Divider
from ...Tray import Tray
from ...Genetic import create_etherfields


# TODO *** Specify the command identity information. ***
CMD_ID = f'{config.COMPANY_NAME}_{config.ADDIN_NAME}_cmdDialog'
CMD_NAME = 'BGO'
CMD_Description = 'BGO components'

# Specify that the command will be promoted to the panel.
IS_PROMOTED = True

# TODO *** Define the location where the command button will be created. ***
# This is done by specifying the workspace, the tab, and the panel, and the 
# command it will be inserted beside. Not providing the command to position it
# will insert it at the end.
WORKSPACE_ID = 'FusionSolidEnvironment'
PANEL_ID = 'SolidScriptsAddinsPanel'
COMMAND_BESIDE_ID = 'ScriptsManagerCommand'

# Resource location for command icons, here we assume a sub folder in this directory named "resources".
ICON_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources', '')

# Local list of event handlers used to maintain a reference so
# they are not released and garbage collected.
local_handlers = []

created_sketches = []

#etherfields = create_etherfields()

# Executed when add-in is run.
def start():
    # Create a command Definition.
    cmd_def = ui.commandDefinitions.addButtonDefinition(CMD_ID, CMD_NAME, CMD_Description, ICON_FOLDER)

    # Define an event handler for the command created event. It will be called when the button is clicked.
    futil.add_handler(cmd_def.commandCreated, command_created)

    # ******** Add a button into the UI so the user can run the command. ********
    # Get the target workspace the button will be created in.
    workspace = ui.workspaces.itemById(WORKSPACE_ID)

    # Get the panel the button will be created in.
    panel = workspace.toolbarPanels.itemById(PANEL_ID)

    # Create the button command control in the UI after the specified existing command.
    control = panel.controls.addCommand(cmd_def, COMMAND_BESIDE_ID, False)

    # Specify if the command is promoted to the main toolbar. 
    control.isPromoted = IS_PROMOTED


# Executed when add-in is stopped.
def stop():
    # Get the various UI elements for this command
    workspace = ui.workspaces.itemById(WORKSPACE_ID)
    panel = workspace.toolbarPanels.itemById(PANEL_ID)
    command_control = panel.controls.itemById(CMD_ID)
    command_definition = ui.commandDefinitions.itemById(CMD_ID)

    # Delete the button command control
    if command_control:
        command_control.deleteMe()

    # Delete the command definition
    if command_definition:
        command_definition.deleteMe()


# Function that is called when a user clicks the corresponding button in the UI.
# This defines the contents of the command dialog and connects to the command related events.
def command_created(args: adsk.core.CommandCreatedEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Created Event')

    # https://help.autodesk.com/view/fusion360/ENU/?contextId=CommandInputs
    inputs = args.command.commandInputs

    # TODO Define the dialog for your command by adding different inputs to the command.

    #inputs.addFloatSliderCommandInput('test','Test', )

    dropdown_input = inputs.addDropDownCommandInput('dropdown','Components', adsk.core.DropDownStyles.TextListDropDownStyle)
    dropdown_input.listItems.add("Divider", True)
    dropdown_input.listItems.add("Tray", False)
    dropdown_input.listItems.add("Game", False)

    #has_label_input = inputs.addBoolValueInput('has_label', 'Has Label', True)

    # Add length, width, height inputs (initially visible)

    length_input = inputs.addValueInput('length', 'Length', 'mm', adsk.core.ValueInput.createByReal(94/10))
    width_input = inputs.addValueInput('width', 'Width', 'mm', adsk.core.ValueInput.createByReal(63.5/10))
    height_input = inputs.addValueInput('height', 'Height', 'mm', adsk.core.ValueInput.createByReal(0.6/10))    

    left_right_input = inputs.addBoolValueInput('left_right', 'Label offset from left', True)
    label_length_input = inputs.addValueInput('label_length', 'Label length', 'mm', adsk.core.ValueInput.createByReal(6/10))
    #label_width_input = inputs.addValueInput('label_width', 'Label width', 'mm', adsk.core.ValueInput.createByReal(63.5/10/4))
    label_width_input = inputs.addFloatSliderCommandInput('label_width', 'Label width(%)', '', 0.0, 0.999)
    #label_offset_input = inputs.addValueInput('label_offset', 'Label offset', 'mm', adsk.core.ValueInput.createByReal(63.5/10/4))
    label_offset_input = inputs.addFloatSliderCommandInput('label_offset', 'Label offset(%)', '', 0.0, 0.999)
    label_fillet_input = inputs.addValueInput('label_fillet', 'Label fillet', 'mm', adsk.core.ValueInput.createByReal(4/10))
    label_text_input = inputs.addTextBoxCommandInput('label_text', 'Label text', 'Label', 1, False)
    label_text_height = inputs.addValueInput('label_text_height', 'Text height', 'mm', adsk.core.ValueInput.createByReal(0.6/10))

    base_thickness_input = inputs.addValueInput('base_thickness', 'Base thickness', 'mm', adsk.core.ValueInput.createByReal(0.02))
    wall_thickness_input = inputs.addValueInput('wall_thickness', 'Wall thickness', 'mm', adsk.core.ValueInput.createByReal(0.02))
    cutout_ratio_input = inputs.addFloatSliderCommandInput('cutout_ratio', 'Cutout ratio(%)', '', 0.0, 0.5)

    # Make length, width, height inputs initially invisible if not "Divider"
    if dropdown_input.selectedItem.name != "Divider" and dropdown_input.selectedItem.name != "Tray":
        length_input.isVisible = False
        width_input.isVisible = False
        height_input.isVisible = False

    if dropdown_input.selectedItem.name != "Divider":
        label_width_input.isVisible = False

    if dropdown_input.selectedItem.name != 'Tray':
        base_thickness_input.isVisible = False
        wall_thickness_input.isVisible = False
        cutout_ratio_input.isVisible = False

    left_right_input.isVisible = False
    label_length_input.isVisible = False
    #label_width_input.isVisible = False
    label_offset_input.isVisible = False
    label_fillet_input.isVisible = False
    label_text_input.isVisible = False
    label_text_height.isVisible = False

    # Create a simple text box input.
    #inputs.addTextBoxCommandInput('text_box', 'Some Text', 'Enter some text.', 1, False)

    # Create a value input field and set the default using 1 unit of the default length unit.
    #defaultLengthUnits = app.activeProduct.unitsManager.defaultLengthUnits
    #default_value = adsk.core.ValueInput.createByString('1')
    #inputs.addValueInput('value_input', 'Some Value', defaultLengthUnits, default_value)


    # TODO Connect to the events that are needed by this command.
    futil.add_handler(args.command.execute, command_execute, local_handlers=local_handlers)
    futil.add_handler(args.command.inputChanged, command_input_changed, local_handlers=local_handlers)
    futil.add_handler(args.command.executePreview, command_preview, local_handlers=local_handlers)
    futil.add_handler(args.command.validateInputs, command_validate_input, local_handlers=local_handlers)
    futil.add_handler(args.command.destroy, command_destroy, local_handlers=local_handlers)

def get_tray(args, offset_x = 0):
    offset_x = 0
    length = 0
    width = 0
    height = 0
    wall_thickness = 0.02
    base_thickness = 0.02
    cutout_ratio = 0
    x = 0
    y = 0
    z = 0

    if hasattr(args, "command"):
        inputs = args.command.commandInputs

        length_input: adsk.core.ValueCommandInput = inputs.itemById('length')
        width_input: adsk.core.ValueCommandInput = inputs.itemById('width')
        height_input: adsk.core.ValueCommandInput = inputs.itemById('height')
        base_thickness_input: adsk.core.ValueCommandInput = inputs.itemById('base_thickness')
        wall_thickness_input: adsk.core.ValueCommandInput = inputs.itemById('wall_thickness')
        cutout_ratio_input: adsk.core.FloatSliderCommandInput = inputs.itemById('cutout_ratio')

        length = length_input.value
        width = width_input.value
        height = height_input.value
        base_thickness = base_thickness_input.value
        wall_thickness = wall_thickness_input.value
        cutout_ratio = cutout_ratio_input.valueOne
    else:
        length = args['Length']
        width = args['Width']
        height = args['Height']        
        x = args['x']
        y = args['y']
        z = args['z']

    tray = Tray(
            Length = length, 
            Width = width, 
            Height = height, 
            WallThickness = wall_thickness,
            BaseThickness = base_thickness,
            CutoutRatio = cutout_ratio,
            x = x + offset_x,
            y = y,
            z = z
    )

    return tray

def get_divider(args: adsk.core.CommandEventArgs):
    inputs = args.command.commandInputs

    length_input: adsk.core.ValueCommandInput = inputs.itemById('length')
    width_input: adsk.core.ValueCommandInput = inputs.itemById('width')
    height_input: adsk.core.ValueCommandInput = inputs.itemById('height')
    #has_label_input: adsk.core.BoolValueCommandInput = inputs.itemById('has_label')
    label_length_input: adsk.core.ValueCommandInput = inputs.itemById('label_length')    
    #label_width_input: adsk.core.ValueCommandInput = inputs.itemById('label_width')
    label_width_input: adsk.core.FloatSliderCommandInput = inputs.itemById('label_width')    
    #label_offset_input: adsk.core.ValueCommandInput = inputs.itemById('label_offset')
    label_offset_input: adsk.core.FloatSliderCommandInput = inputs.itemById('label_offset')    
    label_fillet_input: adsk.core.ValueCommandInput = inputs.itemById('label_fillet')
    left_right_input: adsk.core.BoolValueCommandInput = inputs.itemById('left_right')
    label_text_input: adsk.core.TextBoxCommandInput = inputs.itemById('label_text')            
    label_text_height_input: adsk.core.ValueCommandInput = inputs.itemById('label_text_height')    

    length = length_input.value
    width = width_input.value
    height = height_input.value
    has_label = label_width_input.valueOne > 0
    if has_label:
        divider = Divider(
            Length = length, 
            Width = width, 
            Height = height,
            LabelLeftRight = left_right_input.value,
            LabelOffset = label_offset_input.valueOne * width,
            LabelLength = label_length_input.value,
            LabelWidth = label_width_input.valueOne * width,
            LabelFillet = label_fillet_input.value,
            LabelText = label_text_input.formattedText,
            TextHeight = label_text_height_input.value)
    else:
        divider = Divider(
            Length = length, 
            Width = width, 
            Height = height)
        
    return divider

def cleanup_sketches():
    for sketch in created_sketches:
        if sketch.isValid:
            sketch.deleteMe()
    created_sketches.clear()

# This event handler is called when the user clicks the OK button in the command dialog or 
# is immediately called after the created event not command inputs were created for the dialog.
def command_execute(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Execute Event')

    cleanup_sketches()

    # TODO ******************************** Your code here ********************************

    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs
    dropdown_input: adsk.core.DropDownCommandInput = inputs.itemById('dropdown')    

    if dropdown_input.selectedItem.name == "Divider":
        divider = get_divider(args)
        divider.generate_fusion()
    elif dropdown_input.selectedItem.name == "Tray":
        tray = get_tray(args)
        tray.generate_fusion()
    elif dropdown_input.selectedItem.name == "Game":
        if etherfields is not None:
            offset_x = 0
            sorted_etherfields = sorted(etherfields, key = lambda x: x['x'])
            for el in sorted_etherfields:
                tray = get_tray(el, offset_x)
                tray.generate_fusion()
                offset_x += 1


# This event handler is called when the command needs to compute a new preview in the graphics window.
def command_preview(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Preview Event')
    inputs = args.command.commandInputs

    # Get a reference to your command's inputs.
    inputs = args.command.commandInputs
    dropdown_input: adsk.core.DropDownCommandInput = inputs.itemById('dropdown')    

    if dropdown_input.selectedItem.name == "Divider":
        divider = get_divider(args)
        sketch = divider.create_sketch()
        divider.create_sketch_text(sketch)
        created_sketches.append(sketch)
    elif dropdown_input.selectedItem.name == "Tray":
        tray = get_tray(args)
        sketch = tray.create_sketch()
        created_sketches.append(sketch)
    elif dropdown_input.selectedItem.name == "Game":
        if etherfields is not None:
            offset_x = 0
            sorted_etherfields = sorted(etherfields, key = lambda x: x['x'])
            for el in sorted_etherfields:
                tray = get_tray(el, offset_x)
                sketch = tray.create_sketch()
                created_sketches.append(sketch)
                offset_x += 1


# This event handler is called when the user changes anything in the command dialog
# allowing you to modify values of other inputs based on that change.
def command_input_changed(args: adsk.core.InputChangedEventArgs):
    changed_input = args.input
    inputs = args.inputs

    if changed_input.id == 'dropdown':
        inputs = changed_input.commandInputs
        length_input = inputs.itemById('length')
        width_input = inputs.itemById('width')
        height_input = inputs.itemById('height')
        label_width_input = inputs.itemById('label_width')
        #has_label_input = inputs.itemById('has_label')

        isVisible = changed_input.selectedItem.name == "Divider" or changed_input.selectedItem.name == "Tray"
        length_input.isVisible = isVisible
        width_input.isVisible = isVisible
        height_input.isVisible = isVisible

        # Update visibility based on the dropdown selection
        if changed_input.selectedItem.name == "Divider":
            label_width_input.isVisible = True
        else:
            inputs.itemById('left_right').isVisible = False
            inputs.itemById('label_length').isVisible = False
            inputs.itemById('label_width').isVisible = False
            inputs.itemById('label_offset').isVisible = False
            inputs.itemById('label_fillet').isVisible = False    
            inputs.itemById('label_text').isVisible = False
            inputs.itemById('label_text_height').isVisible = False

        if changed_input.selectedItem.name == "Tray":
            inputs.itemById('base_thickness').isVisible = True
            inputs.itemById('wall_thickness').isVisible = True
            inputs.itemById('cutout_ratio').isVisible = True
        
        #has_label_input.isVisible = isVisible

    #if changed_input.id == 'has_label':        
    if changed_input.id == 'label_width':        
        #changed_input = adsk.core.BoolValueCommandInput.cast(changed_input)
        changed_input = adsk.core.FloatSliderCommandInput.cast(changed_input)
        has_label = changed_input.valueOne > 0
        left_right_input = inputs.itemById('left_right')    
        label_length_input = inputs.itemById('label_length')    
        label_width_input = inputs.itemById('label_width')    
        label_offset_input = inputs.itemById('label_offset')    
        label_fillet_input = inputs.itemById('label_fillet')    
        label_text_input = inputs.itemById('label_text')
        label_text_height_input = inputs.itemById('label_text_height')
        left_right_input.isVisible = has_label
        label_length_input.isVisible = has_label
        #label_width_input.isVisible = has_label
        label_offset_input.isVisible = has_label
        label_fillet_input.isVisible = has_label
        label_text_input.isVisible = has_label
        label_text_height_input.isVisible = has_label

    if changed_input.id == 'label_offset':
        changed_input = adsk.core.FloatSliderCommandInput.cast(changed_input)
        label_width_input = adsk.core.FloatSliderCommandInput.cast(inputs.itemById('label_width'))
        label_width_input.maximumValue = 0.999 - changed_input.valueOne

    if changed_input.id == 'label_width':
        changed_input = adsk.core.FloatSliderCommandInput.cast(changed_input)
        label_offset_input = inputs.itemById('label_offset')    
        label_offset_input.maximumValue = 0.999 - changed_input.valueOne

    # General logging for debug.
    futil.log(f'{CMD_NAME} Input Changed Event fired from a change to {changed_input.id}')


# This event handler is called when the user interacts with any of the inputs in the dialog
# which allows you to verify that all of the inputs are valid and enables the OK button.
def command_validate_input(args: adsk.core.ValidateInputsEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Validate Input Event')

    inputs = args.inputs        

# This event handler is called when the command terminates.
def command_destroy(args: adsk.core.CommandEventArgs):
    # General logging for debug.
    futil.log(f'{CMD_NAME} Command Destroy Event')

    global local_handlers
    local_handlers = []
