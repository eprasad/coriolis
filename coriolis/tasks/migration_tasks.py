# Copyright 2016 Cloudbase Solutions Srl
# All Rights Reserved.

from coriolis import constants
from coriolis.providers import factory as providers_factory
from coriolis import schemas
from coriolis.tasks import base

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


class ExportInstanceTask(base.TaskRunner):
    def run(self, ctxt, instance, origin, destination, task_info,
            event_handler):
        provider = providers_factory.get_provider(
            origin["type"], constants.PROVIDER_TYPE_EXPORT, event_handler)
        connection_info = base.get_connection_info(ctxt, origin)
        export_path = task_info["export_path"]

        export_info = provider.export_instance(
            ctxt, connection_info, instance, export_path)

        # Validate the output
        schemas.validate_value(
            export_info, schemas.CORIOLIS_VM_EXPORT_INFO_SCHEMA)
        task_info["export_info"] = export_info
        task_info["retain_export_path"] = True

        return task_info


class ImportInstanceTask(base.TaskRunner):
    def run(self, ctxt, instance, origin, destination, task_info,
            event_handler):
        target_environment = destination.get("target_environment") or {}
        export_info = task_info["export_info"]

        provider = providers_factory.get_provider(
            destination["type"], constants.PROVIDER_TYPE_IMPORT, event_handler)
        connection_info = base.get_connection_info(ctxt, destination)

        import_info = provider.import_instance(
            ctxt, connection_info, target_environment, instance, export_info)

        task_info["instance_deployment_info"] = import_info[
            "instance_deployment_info"]
        task_info["osmorphing_info"] = import_info.get("osmorphing_info", {})
        task_info["osmorphing_connection_info"] = base.marshal_migr_conn_info(
            import_info["osmorphing_connection_info"])

        task_info["origin_provider_type"] = constants.PROVIDER_TYPE_EXPORT
        task_info["destination_provider_type"] = constants.PROVIDER_TYPE_IMPORT

        return task_info


class FinalizeImportInstanceTask(base.TaskRunner):
    def run(self, ctxt, instance, origin, destination, task_info,
            event_handler):
        provider = providers_factory.get_provider(
            destination["type"], constants.PROVIDER_TYPE_IMPORT, event_handler)
        connection_info = base.get_connection_info(ctxt, destination)
        instance_deployment_info = task_info["instance_deployment_info"]

        provider.finalize_import_instance(
            ctxt, connection_info, instance_deployment_info)

        return task_info


class CleanupFailedImportInstanceTask(base.TaskRunner):
    def run(self, ctxt, instance, origin, destination, task_info,
            event_handler):
        provider = providers_factory.get_provider(
            destination["type"], constants.PROVIDER_TYPE_IMPORT, event_handler)
        connection_info = base.get_connection_info(ctxt, destination)
        instance_deployment_info = task_info.get(
            "instance_deployment_info", {})

        provider.cleanup_failed_import_instance(
            ctxt, connection_info, instance_deployment_info)

        return task_info
