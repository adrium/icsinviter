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

## Example

You can run the example as follows:

	git clone https://github.com/adrium/icsinviter.git
	cd icsinviter/example
	echo '{}' > events.json
	python ../icsinviter.py config.json
	less output.eml

## Configuration

The configuration is read from multiple JSON files and the keys are merged recursively.
Files to be loaded are specified as command line parameters.

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
- If they are filtered (see `filter` parameter)
- For email addresses without an entry in the `feeds` parameter

Note: The file should be initialized manually with `{}` as content.

### feeds

Mapping of configured email addresses to feed links.

Events and updates of the feed are sent to the respective email address.
The tool will keep events of unavailable or invalid feeds.

Hint: To temporarily disable a feed, an invalid feed link could be set.

Hint: This parameter could be set in a different configuration file
for maintenance by another tool.

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
- Filtered events are neither sent nor cancelled

### var

*Default: {}*

Static variables for use in the template.

Built-in variables are:

- `mail_to` contains the email address associated with the feed
- `uuid` a UUID that is generated for every render operation
- `ics` the ics file

Values containing a `%` are used as a format string for [strftime](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior).

### filter

*Default: {}*

Filter events.

The dict consists of event keys and filters.
Filters can be specified as dict with an operator `op` and a value `value` keys.
Operator can be: `<` `>` `=` `~` (regex search)

It is recommended to only include events in the future:

`{ "dtstart": { "op": ">", "value": "%Y%m%d", 'methods': ['request','cancel'] } }`

The `methods` parameter is optional.

Values containing a `%` are used as a format string for [strftime](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior).

### set

*Default: {}*

Update event properties.

The dict consists of keys and values with the name of the event property that should be updated.
Values are interpolated in the same way as templates.

### replace

*Default: {}*

Update event properties.

The dict consists of keys with the name of the event property and a dict containing
a `pattern` and `repl` key that will be used as parameters for a regex replacement.

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
