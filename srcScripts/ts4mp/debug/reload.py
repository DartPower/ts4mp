import os.path
import os

import sims4.commands
from sims4 import reload
from ts4mp.core.mp_utils import get_sims_documents_directory

#use it like Scripts\ts4mp\debug\reload
@sims4.commands.Command('ts4mp.reload', command_type=sims4.commands.CommandType.Live)
def reload_maslow(module: str, _connection=None):
    output = sims4.commands.CheatOutput(_connection)

    try:
        dirname = get_sims_documents_directory() + "Mods/ts4multiplayer"
        filename = os.path.join(dirname, module) + ".py"
        reloaded_module = reload.reload_file(filename)
        output("Reloading {}".format(filename))




        for root, dirnames, filenames in os.walk(dirname):
            for a in range(0, len(filenames)):
                if filenames[a].split("\n")[-1] == module + ".py":
                    filename = filenames[a]
                    output(os.path.join(root, filename))

                    reloaded_module = reload.reload_file(os.path.join(root, filename))
                    output("Reloading {}".format(filename))



        if reloaded_module is not None:
            output("Done reloading!")
        else:
            output("Error loading module or module does not exist")

    except Exception as e:
        output("Reload failed: ")

        for v in e.args:
            output(v)
