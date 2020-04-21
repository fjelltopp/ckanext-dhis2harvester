import logging

logger = logging.getLogger(__name__)


def check_if_response_is_ok(response):
    if 200 < response.status_code >= 300:
        logger.info("Request failed with code %d.", response.status_code)
        try:
            logger.debug(response.json().get("message"), stack_info=True)
            logger.debug(response.text)
        except ValueError:
            logger.debug(response.text, stack_info=True)
            return False
        finally:
            logger.debug("Failed to get valid response")
            return False
    elif "<html class=\"loginPage\">" in response.text:
        logger.debug("Failed with DHIS2 authentication")
        return False
    return True
