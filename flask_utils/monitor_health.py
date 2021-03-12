#!/usr/bin/env python3
"""
Health check API endpoint
"""
# -*- encoding: utf-8 -*-

#============================================================================================
# Imports
#============================================================================================
# Standard imports

# Third-party imports
from flask import make_response, jsonify
from flask_restx import Resource
from flask_accepts import for_swagger
from pyslack.notify import NotificationService

# Local imports
from flask_utils.config_util import get_config
from flask_utils.logger_util import get_common_logger
from flask_utils.db_util import DBUtil
from flask_utils.api_util import api

logger = get_common_logger(__name__)
oracle_config = get_config().db_config
db_util = DBUtil()

ns = api.namespace('monitor',
                   description='Health check endpoint which returns a status 200 and status: '
                               'Pass if the API is up and responsive')

# --------------------------------------------------------------------------------------------
# Schema Objects
# --------------------------------------------------------------------------------------------


class MonitorHealthPassSchema(Schema):
    """
    Schema class for a successful healthcheck
    """
    status = fields.Str(description="PASS", default="PASS")


class MonitorHealthFailSchema(Schema):
    """
    Schema class for a failed healthcheck
    """
    status = fields.Str(description="FAIL", default="FAIL")
    error = fields.Str(
        description="Error encountered",
        default=(
            'The server encountered an internal error and was unable to complete your request. '
            'Either the server is overloaded or there is an error in the application.'
            )
        )

    class Meta:
        """
        Additional configuration for the Marshmallow schema
        """
        ordered = True


@ns.route("/health")
class ApiMonitor(Resource):
    """
    /monitor/health The endpoint verifies the FIN Employee API is available
    """
    # Using multiple @responds annotations for differing schemas is not available yet in Flask_Accepts
    # @responds(schema=MonitorHealthPassSchema, api=api)
    # @responds(schema=MonitorHealthFailSchema, api=api)
    @api.doc(security=None)
    @ns.response(200, 'Success', for_swagger(MonitorHealthPassSchema, ns))
    @ns.response(500, 'Fail', for_swagger(MonitorHealthFailSchema, ns))
    def get(self):
        """
        Get a PASS/FAIL based on API availability and responsiveness
        """
        try:
            pool = db_util.get_session_pool()
            query = "SELECT 1 FROM DUAL"
            response = db_util.execute_query(pool, query)

            if response is not None:
                return jsonify(
                    status="PASS"
                )
            else:
                raise Exception("Error encountered when attempting healthcheck with Oracle Financials database")

        except Exception as err: # pylint: disable=broad-except
            logger.error('API health check failure: %s', err, exc_info=True)
            return make_response(jsonify(
                status="FAIL",
                error=str(err)
            ), 500)


@ns.route("/hello/<string:title>/<string:message>")
class ApiNotificationsTest(Resource):

    def get(self, title, message):
        api_config = get_config().api_config
        notification_service = NotificationService(webhook=api_config["slack_key"],username=api_config["title"])
        notification_service.success(title=title, message=message,link=api_config["app_source"])
        return make_response(jsonify({
            "alert": "sent notification to slack",
            "title": title,
            "message": message,
            "link": api_config["app_source"]
        }))
