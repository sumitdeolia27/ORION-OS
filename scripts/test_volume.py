import runpy

# Load the main script as a module (returns its globals)
module_globals = runpy.run_path('orion_os_navigator.py')

CommandProcessor = module_globals.get('CommandProcessor')
SystemController = module_globals.get('SystemController')

if not CommandProcessor or not SystemController:
    print('Could not load CommandProcessor or SystemController from module')
    raise SystemExit(1)

# Instantiate system controller and a processor (pass None for voice/ai/app to avoid extra threads)
sys_ctrl = SystemController()
processor = CommandProcessor(sys_ctrl, None, None, None)

for cmd in ['volume down', 'volume down', 'volume up', 'take a screenshot']:
    print('---')
    print('Command:', cmd)
    out = processor.process(cmd)
    print('Result:', out)
