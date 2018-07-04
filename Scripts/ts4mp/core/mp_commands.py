import socket

import distributor.system
import persistence_module
import services
import sims4.commands
from protocolbuffers.FileSerialization_pb2 import ZoneObjectData
from server.account import Account
from world.travel_service import travel_sim_to_zone
import sys
from ts4mp.debug.log import ts4mp_log
from ts4mp.core.mp_sync import outgoing_commands, outgoing_lock, ArbritraryFileMessage, get_file_matching_name
import game_services
import zone

@sims4.commands.Command('get_con', command_type=sims4.commands.CommandType.Live)
def get_con(_connection=None):
    output = sims4.commands.CheatOutput(_connection)

    # Gets the current client connection
    output(str(_connection))


@sims4.commands.Command('get_clients', command_type=sims4.commands.CommandType.Live)
def get_clients(_connection=None):
    output = sims4.commands.CheatOutput(_connection)

    # Gets all the current client connections
    clients = services.client_manager()._objects.values()

    for client in clients:
        output(str(client.id))

@sims4.commands.Command('get_cds', command_type=sims4.commands.CommandType.Live)
def get_cds(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    try:
        # Gets all the current client connections
        clients = distributor.system._distributor_instance.client_distributors

        for client in clients:
            output(str(client))
    except Exception as e:
        output(str(e))


@sims4.commands.Command('add_client_sims', command_type=sims4.commands.CommandType.Live)
def add_client_sims(_connection=None):
    output = sims4.commands.CheatOutput(_connection)

    # Add the first client's selectable sims to the new client's. Only expects one multiplayer client at the moment.
    client = services.client_manager().get(1000)
    first_client = services.client_manager().get_first_client()

    for sim_info in first_client._selectable_sims:
        client._selectable_sims.add_selectable_sim_info(sim_info)

    client.set_next_sim()




@sims4.commands.Command('rem', command_type=sims4.commands.CommandType.Live)
def rem(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    output("Attempting to remove client")

    # Forcefully remove the multiplayer client. Only supports one multiplayer client at the moment.
    distributor.system._distributor_instance.remove_client_from_id(1000)
    client_manager = services.client_manager()
    client = client_manager.get(1000)
    client_manager.remove(client)

    output("Removed client")


@sims4.commands.Command('get_name', command_type=sims4.commands.CommandType.Live)
def get_name(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    output(str(socket.gethostname()))


@sims4.commands.Command('load_zone', command_type=sims4.commands.CommandType.Live)
def load_zone(_connection=None):
    try:
        zone = services.current_zone()
        name = str(hex(zone.id)).replace("0x", "")
        zone_objects_pb = ZoneObjectData()

        (file_path, _) = get_file_matching_name(name)
        zone_objects_message = open(file_path, "rb").read()

        ts4mp_log("msg", dir(zone_objects_pb))

        zone_objects_pb.ParseFromString(zone_objects_message)

        ts4mp_log("msg", zone_objects_pb)
        ts4mp_log("msg", zone_objects_message)

        persistence_module.run_persistence_operation(persistence_module.PersistenceOpType.kPersistenceOpLoadZoneObjects, zone_objects_pb, 0, None)
    except Exception as e:
        ts4mp_log("er", e)


@sims4.commands.Command('travel', command_type=sims4.commands.CommandType.Live)
def travel(_connection=None):
    client = services.client_manager().get_first_client()
    zone = services.current_zone()

    travel_sim_to_zone(client.active_sim.id, zone.id)


@sims4.commands.Command('get_zone', command_type=sims4.commands.CommandType.Live)
def get_zone_id(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    zone = services.current_zone()

    output(str(zone.id))


@sims4.commands.Command('send_lot_architecture_and_reload', command_type=sims4.commands.CommandType.Live)
def send_lot_architecture_and_reload(_connection=None):
    output = sims4.commands.CheatOutput(_connection)
    output("working")

    zone = services.current_zone()
    name = str(hex(zone.id)).replace("0x", "")

    ts4mp_log("zone_id", "{}, {}".format(name, zone.id))

    (file_path, file_name) = get_file_matching_name(name)

    if file_path is not None:
        with outgoing_lock:
            ts4mp_log("zone_id", "{}, {}".format(file_path, file_name))
            msg = ArbritraryFileMessage(name, open(file_path, "rb").read())
            outgoing_commands.append(msg)


@sims4.commands.Command('change_persona', command_type=sims4.commands.CommandType.Live)
def change_persona(name: str, _connection=None):
    output = sims4.commands.CheatOutput(_connection)
    client = services.client_manager().get_first_client()

    client._account._persona_name = name
    output("Your new persona name is: {}".format(client._account._persona_name))


@sims4.commands.Command('change_client_persona', command_type=sims4.commands.CommandType.Live)
def change_client_persona(name: str, _connection=None):
    output = sims4.commands.CheatOutput(_connection)
    client = services.client_manager().get_client_by_account(1000)
    if client is None:
        output("That's odd, there's no multiplayer client, even though it should be always on.")
        return

    client._account._persona_name = name
    output("The client's new persona name is: {}".format(client._account._persona_name))

from situations.base_situation import BaseSituation
@sims4.commands.Command('debug_objects_in_view', command_type=sims4.commands.CommandType.Live)
def get_objects_in_view_gen(_connection=None):
    all_objs = []
    for manager in services.client_object_managers():
        for obj in manager.get_all():
            #if issubclass(type(obj), BaseSituation):
                all_objs.append(type(obj))
    ts4mp_log("objs in view", str(all_objs))


