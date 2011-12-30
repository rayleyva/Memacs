# -*- coding: utf-8 -*-
# Time-stamp: <2011-12-30 00:30:57 armin>

import time
import logging
from email import message_from_string
from email.utils import parsedate
from common.orgproperty import OrgProperties
from common.orgformat import OrgFormat


class MailHandler(object):
    
    @staticmethod 
    def get_value_or_empty_str(headers, key, remove_newline=False):
        """
        @param return: headers[key] if exist else ""
        """
        ret = ""
        if key in headers:
            ret = headers[key]
            if remove_newline:
                ret = ret.replace("\n", "")
        return ret
        

    @staticmethod
    def handle_message(message,
                       add_body=False):
        """
        parses whole mail from string 
        
        @param message: mail message
        @param add_body: if specified, body is added
        @return values for OrgWriter.write_org_subitem
        """

        msg = message_from_string(message)

        # Read only these fields
        use_headers = ["To",
                       "Date",
                       "From",
                       "Subject",
                       "Reply-To",
                       "Newsgroups",
                       "Cc",
                       ]
        # These fields are added, if found to :PROPERTIES: drawer
        not_properties = ["Date",
                          "Subject",
                          "From"
                          ]

        properties = OrgProperties()
        headers = {}

        logging.debug("Message items:")
        logging.debug(msg.items())

        # fill headers and properties
        for key, value in msg.items():
            value = value.replace("\r", "").decode('utf-8')
            if key in use_headers:
                headers[key] = value
                if key not in not_properties:
                    properties.add(key, value.replace("\n", ""))
            if key == "Message-ID":
                properties.set_id(value)

        notes = ""
        # look for payload
        # if more than one payload, use text/plain payload
        if add_body:
            payload = msg.get_payload()
            if payload.__class__ == list:
                # default use payload[0]
                payload_msg = payload[0].get_payload()
                for payload_id in len(payload):
                    for param in payload[payload_id].get_params():
                        if param[0] == 'text/plain':
                            payload_msg = payload[payload_id].get_payload()
                            break
                    if payload_msg != payload[0].get_payload():
                        break
                notes = payload_msg
            else:
                notes = payload

        notes = notes.replace("\r", "").decode('utf-8')
        output_from = MailHandler.get_value_or_empty_str(headers, "From")
        subject = MailHandler.get_value_or_empty_str(headers, "subject", True)
        
        dt = MailHandler.get_value_or_empty_str(headers, "Date", False)
        timestamp = ""
        if dt != "":
            try:
                time_tupel = time.localtime(time.mktime(parsedate(dt)))
                timestamp = OrgFormat.datetime(time_tupel)
            except TypeError:
                logging.error("could not parse datime from msg %s", subject)
            
        
        if "Newsgroups" in headers:
            ng_list = []
            for ng in headers["Newsgroups"].split(","):
                ng_list.append(OrgFormat.newsgroup_link(ng))
            output_ng = ", ".join(map(str, ng_list))
            output = output_from + u"@" + output_ng + ": " + subject
        else:
            output = output_from + u": " + subject

        return timestamp, output, notes, properties