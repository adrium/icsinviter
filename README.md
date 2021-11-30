# icsinviter

Send calendar invites via email based on calendar feeds.

Support includes:

- humanity.com
- doodle.com
- ferienwiki.de
- calendarlabs.com

## Description

Microsoft Outlook does not display subscribed calendar (ics) feeds
to other people even though they have access to the personal calendar.
To work around this limitation, this tool fetches feeds for multiple people,
turns the feed into seperate events, and sends them as meeting invitation emails.
It keeps track of the sent invitations and sends updates or cancellations.

Originally created for a team of 150+ people scheduled using humanity.com,
the tool supports multiple ics feed publishers thanks to a flexible configuration system.
Technically, other actions than sending emails could be triggered based on changes in the feed.

## Configuration

The configuration is read from multiple JSON files and the top level keys are merged.
Files are loaded from `config/*.json` in arbitrary order.

The configuration can be split into multiple files.
This allows for example to set permissions on the `cmd` parameters,
or update part of it easily, such as the `feeds` list.

A complete example can be found in [example/config.json](example/config.json).

All configuration parameters are described in the following sections.

### events

Filename of the state file.

Copies of sent events and updates to the configured email addresses
are written to this JSON file.

The tool removes events:

- After a cancellation is sent
- If they are considered old (see `dtstartfilter` parameter)
- For email addresses without an entry in the `feeds` parameter

Note: The file should be initialized manually with `{}` as content.

### feeds

Mapping of configured email addresses to feed links.

Events and updates of the feed are sent to the respective email address.

- The `mail_to` template variable is set accordingly (see `var` dict)
- The tool will keep events of unavailable or invalid feeds

Hint: To temporarily disable a feed, an invalid feed link could be set.

Hint: This parameter could be set in a different configuration file
for maintenance by another tool.

### dtstartfilter

Filter old events.

The `DTSTART` property of events is string-compared to this value.
Events with smaller values are considered old and are ignored.

The value is copied into the `var` dict and can be used as time format.

### cmd

External tools to retrieve feeds and send emails.

Non-zero exit codes or messages on `stderr` are treated as a failure.

#### cmd.download

Feed retrieval shell command.

- Receives the URL as last parameter
- Is expected to return the content on `stdout`

#### cmd.sendmail

Email delivery shell command.

- Receives the content of the email on `stdin`
- `stdout` is ignored

### template

Templates for sending emails.

The configuration parameter is a dict with two keys:
`request` and `cancel` and a filename as value.

The templates are interpolated using [str.format](https://docs.python.org/3/library/stdtypes.html#str.format) and the `var` dict.
Additionally, all properties of the `VCALENDAR` and `VEVENT` properties are available in the templates.

### uid

*Default: "uid"*

Event key.

- Events are identified by this property and compared with events in the state file
- New events in the feed are sent
- Missing events in the feed are cancelled
- Old events that are in the past are neither sent nor cancelled

### var

*Default: {}*

Static variables for use in the template.

Values containing a `%` are used as a format string for [time.strftime](https://docs.python.org/3/library/time.html#time.strftime).

### update

*Default: {}*

Update event properties.

The dict consists of keys with the name of the event property that should be updated, and update instructions as values.
The [example/config.json](example/config.json) contains an elaborate example.

### compare

*Default: []*

Detect event updates.

Compare the listed properties and send an event update, if any of those changed.

Note: Comparison should not be done using updated properties.

## Parser

The included parser can be used seperately:

```python
icsinviter.imcToDict(imc, suffix = '_p')
icsinviter.dictToImc(imcdict, suffix = '_p')
```

IMC stands for Internet Mail Consortium, the original creators of the iCalendar and vCard formats.
The parser is flexible and can handle any input that "looks" like any of the formats above.

- Arrays of objects are created with a `BEGIN:NAME` and a matching `END:NAME` definition
- Property parameters are stored in a dict named like the property name with the suffix appended

There are some caveats:

- Multiple equally-named properties can not be handled
- Quoting and encodings are not supported

An example can be found in [testdata/arbitrary.ics](testdata/arbitrary.ics).
It will be turned into [testdata/arbitrary.json](testdata/arbitrary.json) and vice-versa.
