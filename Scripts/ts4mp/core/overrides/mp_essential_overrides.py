import omega
import server.client
import services
import sims4.commands
from server_commands.clock_commands import set_speed, request_pause, unrequest_pause, toggle_pause_unpause
from server_commands.interaction_commands import has_choices, generate_choices, generate_phone_choices, select_choice, cancel_mixer_interaction, cancel_super_interaction, push_interaction
from server_commands.lighting_commands import set_color_and_intensity
from server_commands.sim_commands import set_active_sim
from server_commands.ui_commands import ui_dialog_respond, ui_dialog_pick_result, ui_dialog_text_input
from sims4 import core_services
import game_services
import time_service
import time
import ts4mp.core.mp_sync
import distributor
from server_commands.career_commands import find_career, select_career


from time_service import logger
from ts4mp.core.csn import mp_chat
from ts4mp.utils.native.decorator import decorator
from ts4mp.debug.log import ts4mp_log
from ts4mp.core.mp_sync import ProtocolBufferMessage, outgoing_lock, outgoing_commands, client_sync, server_sync
from ts4mp.utils.native.undecorated import undecorated
from server_commands.argument_helpers import  RequiredTargetParam

COMMAND_FUNCTIONS = {
    'interactions.has_choices'        : has_choices,
    'interactions.choices'            : generate_choices,
    'interactions.phone_choices'      : generate_phone_choices,
    'interactions.select'             : select_choice,
    'interactions.cancel'             : cancel_mixer_interaction,
    'interactions.cancel_si'          : cancel_super_interaction,
    'interactions.push'               : push_interaction,
    'clock.setspeed'                  : set_speed,
    'clock.request_pause'             : request_pause,
    'clock.pause'                     : request_pause,
    'clock.unrequest_pause'           : unrequest_pause,
    'clock.unpause'                   : unrequest_pause,
    'clock.toggle_pause_unpause'      : toggle_pause_unpause,
    'sims.set_active'                 : set_active_sim,
    'mp_chat'                         : mp_chat,
    'ui.dialog.respond'               : ui_dialog_respond,
    'ui.dialog.pick_result'           : ui_dialog_pick_result,
    'ui.dialog.text_input'            : ui_dialog_text_input,
    'lighting.set_color_and_intensity': set_color_and_intensity,
    "careers.find_career"             : find_career,
    "careers.select"                  : select_career
}


def send_message_server(self, msg_id, msg):
    # Send message override for the server.
    # This overrides it so any message for a client with an id of 1000 gets packed into a Message and is placed in the outgoing_commands list for
    # sending out to the multiplayer clients.
    # Only supports one multiplayer client at the moment.
    ts4mp_log("network", "Sending message to client id: {}".format(self.id))

    if self.id != 1000:
        if self.active:
            omega.send(self.id, msg_id, msg.SerializeToString())
        # ts4mp_log_debug("msg", msg)
    else:
        message = ProtocolBufferMessage(msg_id, msg.SerializeToString())
        ts4mp_log("locks", "acquiring outgoing lock")

        # We use a lock here because outgoing_commands is also being altered by the client socket thread.
        with outgoing_lock:
            outgoing_commands.append(message)
        ts4mp_log("network", "Queueing outgoing command for {}".format(self.id))

        ts4mp_log("locks", "releasing outgoing lock")


def send_message_client(self, msg_id, msg):
    # Send Message override for the client.
    # We don't want any of the original server sending stuff to the client.
    # So we override it to do absolutely nothing.
    pass

import time
@decorator
def wrapper_client(func, *args, **kwargs):
    # Wrapper for functions that have their data needed to be sent to the server.
    # This is used for client commands so the server can respond.
    # For example, selecting a choice from the pie menu.
    # Only supports one multiplayer client at the moment.

    ts4mp_log("locks", "acquiring outgoing lock")

    with outgoing_lock:
        # TODO: You should not be referring to a global variable that is in a different module
        parsed_args = []
        for arg in args:
            if isinstance(arg, RequiredTargetParam):
                arg = arg.target_id
            parsed_args.append(arg)
        ts4mp_log("arg_handler", "\n" + str(func.__name__) + ", " + str(parsed_args) + "  " + str(kwargs), force=False)
        outgoing_commands.append("\n" + str(func.__name__) + ", " + str(parsed_args) + "  " + str(kwargs))
    # we sleep here so the networking threads can send the commands, if you remove this, it will make the response times
    # higher
    time.sleep(0.2)

    def do_nothing():
        pass

    return do_nothing

    # ts4mp_log_debug("locks", "releasing outgoing lock")


def on_tick_client():
    # On Tick override for the client.
    # If the service manager hasn't been initialized, return because we don't even have a client manager yet.
    # If we don't have any client, that means we aren't in a zone yet.
    # If we do have at least one client, that means we are in a zone and can sync information.
    service_manager = game_services.service_manager
    ts4mp.core.mp_sync.client_online = False

    if service_manager is None:
        return

    client_manager = services.client_manager()

    if client_manager is None:
        return

    client = client_manager.get_first_client()

    if client is None:
        return
    ts4mp.core.mp_sync.client_online = True

    client_sync()


def on_tick_server():
    # On Tick override for the client.
    # If the service manager hasn't been initialized, return because we don't even have a client manager yet.
    # If we don't have any client, that means we aren't in a zone yet.
    # If we do have at least one client, that means we are in a zone and can sync information.
    service_manager = game_services.service_manager
    if service_manager is None:
        return

    client_manager = services.client_manager()

    if client_manager is None:
        return

    client = client_manager.get_first_client()

    if client is None:
        return

    server_sync()


def update(self, time_slice=True):
    ts4mp_log("simulate", "Client is online?: {}".format(ts4mp.core.mp_sync.client_online), force=False)

    if ts4mp.core.mp_sync.client_online:
        # ts4mp_log("simulate", "Client is online?: {}".format(ts4mp.core.mp_essential.client_online), force=True)

        return
    max_time_ms = self.MAX_TIME_SLICE_MILLISECONDS if time_slice else None
    t1 = time.time()
    result = self.sim_timeline.simulate(services.game_clock_service().now(), max_time_ms=max_time_ms)
    t2 = time.time()

    # ts4mp_log("simulate", "{} ms".format((t2 - t1) * 1000), force=True)
    if not result:
        logger.debug('Did not finish processing Sim Timeline. Current element: {}', self.sim_timeline.heap[0])
    result = self.wall_clock_timeline.simulate(services.server_clock_service().now())
    if not result:
        logger.error('Too many iterations processing wall-clock Timeline. Likely culprit: {}', self.wall_clock_timeline.heap[0])


from ts4mp.configs.server_config import MULTIPLAYER_MOD_ENABLED

if MULTIPLAYER_MOD_ENABLED:
    server.client.Client.send_message = send_message_server

def override_functions_depending_on_client_or_not(is_client):
    if is_client:
        #server.client.Client.send_message = send_message_client
        core_services.on_tick = on_tick_client
        time_service.TimeService.update = update
        for function_command_name, command_function in COMMAND_FUNCTIONS.items():
            sims4.commands.Command(function_command_name, command_type=sims4.commands.CommandType.Live)(wrapper_client(undecorated(command_function)))
    else:
        core_services.on_tick = on_tick_server

