# Copyright 2021-2022 Canonical Ltd.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License version 3 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import textwrap
from unittest.mock import patch

import pytest

from craft_cli.dispatcher import CommandGroup, Dispatcher
from craft_cli.errors import ArgumentParsingError, ProvideHelpException
from craft_cli.helptexts import HelpBuilder
from tests.factory import create_command


@pytest.fixture(autouse=True)
def init_emitter(_init_emitter):
    """Enable the init emitter fixture automatically for all this module."""


# -- building "usage" help


def test_get_usage_message_with_command():
    """Check the general "usage" text passing a command."""
    help_builder = HelpBuilder("testapp", "general summary", [])
    text = help_builder.get_usage_message("bad parameter for build", "build")
    expected = textwrap.dedent(
        """\
        Usage: testapp [options] command [args]...
        Try 'testapp build -h' for help.

        Error: bad parameter for build
    """
    )
    assert text == expected


def test_get_usage_message_no_command():
    """Check the general "usage" text when not passing a command."""
    help_builder = HelpBuilder("testapp", "general summary", [])
    text = help_builder.get_usage_message("missing a mandatory command")
    expected = textwrap.dedent(
        """\
        Usage: testapp [options] command [args]...
        Try 'testapp -h' for help.

        Error: missing a mandatory command
    """
    )
    assert text == expected


# -- building of the big help text outputs


def test_default_help_text():
    """All different parts for the default help."""
    cmd1 = create_command("cmd1", "Cmd help which is very long but whatever.", common=True)
    cmd2 = create_command("command-2", "Cmd help.", common=True)
    cmd3 = create_command("cmd3", "Extremely " + "super crazy long " * 5 + " help.", common=True)
    cmd4 = create_command("cmd4", "Some help.")
    cmd5 = create_command("cmd5", "More help.")
    cmd6 = create_command("cmd6-really-long", "More help.", common=True)
    cmd7 = create_command("cmd7", "More help.")

    command_groups = [
        CommandGroup("group1", [cmd6, cmd2]),
        CommandGroup("group3", [cmd7]),
        CommandGroup("group2", [cmd3, cmd4, cmd5, cmd1]),
    ]
    fake_summary = textwrap.dedent(
        """
        This is the summary for
        the whole program.
    """
    )
    global_options = [
        ("-h, --help", "Show this help message and exit."),
        ("-q, --quiet", "Only show warnings and errors, not progress."),
    ]

    help_builder = HelpBuilder("testapp", fake_summary, command_groups)
    text = help_builder.get_full_help(global_options)

    expected = textwrap.dedent(
        """\
        Usage:
            testapp [help] <command>

        Summary:
            This is the summary for
            the whole program.

        Global options:
                  -h, --help:  Show this help message and exit.
                 -q, --quiet:  Only show warnings and errors, not progress.

        Starter commands:
                        cmd1:  Cmd help which is very long but whatever.
                        cmd3:  Extremely super crazy long super crazy long super
                               crazy long super crazy long super crazy long
                               help.
            cmd6-really-long:  More help.
                   command-2:  Cmd help.

        Commands can be classified as follows:
                      group1:  cmd6-really-long, command-2
                      group2:  cmd1, cmd3, cmd4, cmd5
                      group3:  cmd7

        For more information about a command, run 'testapp help <command>'.
        For a summary of all commands, run 'testapp help --all'.
    """
    )
    assert text == expected


def test_detailed_help_text():
    """All different parts for the detailed help, showing all commands."""
    cmd1 = create_command("cmd1", "Cmd help which is very long but whatever.", common=True)
    cmd2 = create_command("command-2", "Cmd help.", common=True)
    cmd3 = create_command("cmd3", "Extremely " + "super crazy long " * 5 + " help.", common=True)
    cmd4 = create_command("cmd4", "Some help.")
    cmd5 = create_command("cmd5", "More help.")
    cmd6 = create_command("cmd6-really-long", "More help.", common=True)
    cmd7 = create_command("cmd7", "More help.")

    command_groups = [
        CommandGroup("Group 1 description", [cmd6, cmd2]),
        CommandGroup("Group 3 help text", [cmd7]),
        CommandGroup("Group 2 stuff", [cmd3, cmd4, cmd5, cmd1]),
    ]
    fake_summary = textwrap.dedent(
        """
        This is the summary for
        the whole program.
    """
    )
    global_options = [
        ("-h, --help", "Show this help message and exit."),
        ("-q, --quiet", "Only show warnings and errors, not progress."),
    ]

    help_builder = HelpBuilder("testapp", fake_summary, command_groups)
    text = help_builder.get_detailed_help(global_options)

    expected = textwrap.dedent(
        """\
        Usage:
            testapp [help] <command>

        Summary:
            This is the summary for
            the whole program.

        Global options:
                  -h, --help:  Show this help message and exit.
                 -q, --quiet:  Only show warnings and errors, not progress.

        Commands can be classified as follows:

        Group 1 description:
            cmd6-really-long:  More help.
                   command-2:  Cmd help.

        Group 3 help text:
                        cmd7:  More help.

        Group 2 stuff:
                        cmd3:  Extremely super crazy long super crazy long super
                               crazy long super crazy long super crazy long
                               help.
                        cmd4:  Some help.
                        cmd5:  More help.
                        cmd1:  Cmd help which is very long but whatever.

        For more information about a specific command, run 'testapp help <command>'.
    """
    )
    assert text == expected


def test_command_help_text_no_parameters():
    """All different parts for a specific command help that doesn't have parameters."""
    overview = textwrap.dedent(
        """
        Quite some long text.

        Multiline!
    """
    )
    cmd1 = create_command("somecommand", "Command one line help.", overview=overview)
    cmd2 = create_command("other-cmd-2", "Some help.")
    cmd3 = create_command("other-cmd-3", "Some help.")
    cmd4 = create_command("other-cmd-4", "Some help.")
    command_groups = [
        CommandGroup("group1", [cmd1, cmd2, cmd4]),
        CommandGroup("group2", [cmd3]),
    ]

    options = [
        ("-h, --help", "Show this help message and exit."),
        ("-q, --quiet", "Only show warnings and errors, not progress."),
        ("--name", "The name of the charm."),
        ("--revision", "The revision to release (defaults to latest)."),
    ]

    help_builder = HelpBuilder("testapp", "general summary", command_groups)
    text = help_builder.get_command_help(cmd1(None), options)

    expected = textwrap.dedent(
        """\
        Usage:
            testapp somecommand [options]

        Summary:
            Quite some long text.

            Multiline!

        Options:
             -h, --help:  Show this help message and exit.
            -q, --quiet:  Only show warnings and errors, not progress.
                 --name:  The name of the charm.
             --revision:  The revision to release (defaults to latest).

        See also:
            other-cmd-2
            other-cmd-4

        For a summary of all commands, run 'testapp help --all'.
    """
    )
    assert text == expected


def test_command_help_text_with_parameters():
    """All different parts for a specific command help that has parameters."""
    overview = textwrap.dedent(
        """
        Quite some long text.
    """
    )
    cmd1 = create_command("somecommand", "Command one line help.", overview=overview)
    cmd2 = create_command("other-cmd-2", "Some help.")
    command_groups = [
        CommandGroup("group1", [cmd1, cmd2]),
    ]

    options = [
        ("-h, --help", "Show this help message and exit."),
        ("name", "The name of the charm."),
        ("--revision", "The revision to release (defaults to latest)."),
        ("extraparam", "Another parameter.."),
        ("--other-option", "Other option."),
    ]

    help_builder = HelpBuilder("testapp", "general summary", command_groups)
    text = help_builder.get_command_help(cmd1(None), options)

    expected = textwrap.dedent(
        """\
        Usage:
            testapp somecommand [options] <name> <extraparam>

        Summary:
            Quite some long text.

        Options:
                -h, --help:  Show this help message and exit.
                --revision:  The revision to release (defaults to latest).
            --other-option:  Other option.

        See also:
            other-cmd-2

        For a summary of all commands, run 'testapp help --all'.
    """
    )
    assert text == expected


def test_command_help_text_loneranger():
    """All different parts for a specific command that's the only one in its group."""
    overview = textwrap.dedent(
        """
        Quite some long text.
    """
    )
    cmd1 = create_command("somecommand", "Command one line help.", overview=overview)
    cmd2 = create_command("other-cmd-2", "Some help.")
    command_groups = [
        CommandGroup("group1", [cmd1]),
        CommandGroup("group2", [cmd2]),
    ]

    options = [
        ("-h, --help", "Show this help message and exit."),
        ("-q, --quiet", "Only show warnings and errors, not progress."),
    ]

    help_builder = HelpBuilder("testapp", "general summary", command_groups)
    text = help_builder.get_command_help(cmd1(None), options)

    expected = textwrap.dedent(
        """\
        Usage:
            testapp somecommand [options]

        Summary:
            Quite some long text.

        Options:
             -h, --help:  Show this help message and exit.
            -q, --quiet:  Only show warnings and errors, not progress.

        For a summary of all commands, run 'testapp help --all'.
    """
    )
    assert text == expected


# -- real execution outputs


def test_tool_exec_no_arguments_help():
    """Execute the app without any option at all."""
    dispatcher = Dispatcher("testapp", [])
    with patch("craft_cli.helptexts.HelpBuilder.get_full_help") as mock:
        mock.return_value = "test help"
        with pytest.raises(ArgumentParsingError) as exc_cm:
            dispatcher.pre_parse_args([])
    error = exc_cm.value

    # check the given information to the help text builder
    args = mock.call_args[0]
    assert sorted(x[0] for x in args[0]) == [
        "-h, --help",
        "-q, --quiet",
        "-t, --trace",
        "-v, --verbose",
    ]

    # check the result of the full help builder is what is shown
    assert str(error) == "test help"


@pytest.mark.parametrize(
    "sysargv",
    [
        ["-h"],
        ["--help"],
        ["help"],
    ],
)
def test_tool_exec_full_help(sysargv):
    """Execute the app explicitly asking for help."""
    dispatcher = Dispatcher("testapp", [])
    with patch("craft_cli.helptexts.HelpBuilder.get_full_help") as mock:
        mock.return_value = "test help"
        with pytest.raises(ProvideHelpException) as exc_cm:
            dispatcher.pre_parse_args(sysargv)

    # check the result of the full help builder is what is transmitted
    assert str(exc_cm.value) == "test help"

    # check the given information to the help text builder
    args = mock.call_args[0]
    assert sorted(x[0] for x in args[0]) == [
        "-h, --help",
        "-q, --quiet",
        "-t, --trace",
        "-v, --verbose",
    ]


def test_tool_exec_command_incorrect_no_similar():
    """Execute a command that doesn't exist."""
    dispatcher = Dispatcher("testapp", [], summary="general summary")
    with pytest.raises(ArgumentParsingError) as exc_cm:
        dispatcher.pre_parse_args(["wrongcommand"])

    expected = textwrap.dedent(
        """\
        Usage: testapp [options] command [args]...
        Try 'testapp -h' for help.

        Error: no such command 'wrongcommand'
        """
    )

    error = exc_cm.value
    assert str(error) == expected


def test_tool_exec_command_incorrect_similar_one():
    """The command does not exist but is very similar to another one."""
    cmd1 = create_command("abcdefg", "Command line help.")
    cmd2 = create_command("othercommand", "Command line help.")
    command_groups = [CommandGroup("group", [cmd1, cmd2])]
    dispatcher = Dispatcher("testapp", command_groups, summary="general summary")
    with pytest.raises(ArgumentParsingError) as exc_cm:
        dispatcher.pre_parse_args(["abcefg"])  # note missing 'd'

    expected = textwrap.dedent(
        """\
        Usage: testapp [options] command [args]...
        Try 'testapp -h' for help.

        Error: no such command 'abcefg', maybe you meant 'abcdefg'
        """
    )
    assert str(exc_cm.value) == expected


def test_tool_exec_command_incorrect_similar_two():
    """The command does not exist but is very similar to other two."""
    cmd1 = create_command("abcdefg", "Command line help.")
    cmd2 = create_command("abcdefh", "Command line help.")
    cmd3 = create_command("othercommand", "Command line help.")
    command_groups = [CommandGroup("group", [cmd1, cmd2, cmd3])]
    dispatcher = Dispatcher("testapp", command_groups, summary="general summary")
    with pytest.raises(ArgumentParsingError) as exc_cm:
        dispatcher.pre_parse_args(["abcef"])  # note missing 'd'

    expected = textwrap.dedent(
        """\
        Usage: testapp [options] command [args]...
        Try 'testapp -h' for help.

        Error: no such command 'abcef', maybe you meant 'abcdefh' or 'abcdefg'
        """
    )
    assert str(exc_cm.value) == expected


def test_tool_exec_command_incorrect_similar_several():
    """The command does not exist but is very similar to several others."""
    cmd1 = create_command("abcdefg", "Command line help.")
    cmd2 = create_command("abcdefh", "Command line help.")
    cmd3 = create_command("abcdefi", "Command line help.")
    command_groups = [CommandGroup("group", [cmd1, cmd2, cmd3])]
    dispatcher = Dispatcher("testapp", command_groups, summary="general summary")
    with pytest.raises(ArgumentParsingError) as exc_cm:
        dispatcher.pre_parse_args(["abcef"])  # note missing 'd'

    expected = textwrap.dedent(
        """\
        Usage: testapp [options] command [args]...
        Try 'testapp -h' for help.

        Error: no such command 'abcef', maybe you meant 'abcdefi', 'abcdefh' or 'abcdefg'
        """
    )
    assert str(exc_cm.value) == expected


@pytest.mark.parametrize(
    "sysargv",
    [
        ["-h", "wrongcommand"],
        ["wrongcommand", "-h"],
        ["--help", "wrongcommand"],
        ["wrongcommand", "--help"],
        ["-h", "wrongcommand", "--help"],
    ],
)
def test_tool_exec_help_on_command_incorrect(sysargv):
    """Execute a command that doesn't exist."""
    dispatcher = Dispatcher("testapp", [], summary="general summary")
    with pytest.raises(ArgumentParsingError) as exc_cm:
        dispatcher.pre_parse_args(sysargv)

    expected = textwrap.dedent(
        """\
        Usage: testapp [options] command [args]...
        Try 'testapp -h' for help.

        Error: command 'wrongcommand' not found to provide help for
        """
    )

    error = exc_cm.value
    assert str(error) == expected


@pytest.mark.parametrize(
    "sysargv",
    [
        ["-h", "foo", "bar"],
        ["foo", "-h", "bar"],
        ["foo", "bar", "-h"],
        ["--help", "foo", "bar"],
        ["foo", "--help", "bar"],
        ["foo", "bar", "--help"],
        ["help", "foo", "bar"],
    ],
)
def test_tool_exec_help_on_too_many_things(sysargv):
    """Trying to get help on too many items."""
    dispatcher = Dispatcher("testapp", [], summary="general summary")
    with pytest.raises(ArgumentParsingError) as exc_cm:
        dispatcher.pre_parse_args(sysargv)

    expected = textwrap.dedent(
        """\
        Usage: testapp [options] command [args]...
        Try 'testapp -h' for help.

        Error: Too many parameters when requesting help; pass a command, '--all', or leave it empty
        """
    )

    error = exc_cm.value
    assert str(error) == expected


@pytest.mark.parametrize("help_option", ["-h", "--help"])
def test_tool_exec_command_dash_help_simple(help_option):
    """Execute a command (that needs no params) asking for help."""
    cmd = create_command("somecommand", "This command does that.")
    command_groups = [CommandGroup("group", [cmd])]
    dispatcher = Dispatcher("testapp", command_groups)

    with patch("craft_cli.helptexts.HelpBuilder.get_command_help") as mock:
        mock.return_value = "test help"
        with pytest.raises(ProvideHelpException) as exc_cm:
            dispatcher.pre_parse_args(["somecommand", help_option])

    # check the result of the full help builder is what is transmitted
    assert str(exc_cm.value) == "test help"

    # check the given information to the help text builder
    args = mock.call_args[0]
    assert args[0].__class__ == cmd
    assert sorted(x[0] for x in args[1]) == [
        "-h, --help",
        "-q, --quiet",
        "-t, --trace",
        "-v, --verbose",
    ]


@pytest.mark.parametrize("help_option", ["-h", "--help"])
def test_tool_exec_command_dash_help_reverse(help_option):
    """Execute a command (that needs no params) asking for help."""
    cmd = create_command("somecommand", "This command does that.")
    command_groups = [CommandGroup("group", [cmd])]
    dispatcher = Dispatcher("testapp", command_groups)

    with patch("craft_cli.helptexts.HelpBuilder.get_command_help") as mock:
        mock.return_value = "test help"
        with pytest.raises(ProvideHelpException) as exc_cm:
            dispatcher.pre_parse_args([help_option, "somecommand"])

    # check the result of the full help builder is what is transmitted
    assert str(exc_cm.value) == "test help"

    # check the given information to the help text builder
    args = mock.call_args[0]
    assert args[0].__class__ == cmd
    assert sorted(x[0] for x in args[1]) == [
        "-h, --help",
        "-q, --quiet",
        "-t, --trace",
        "-v, --verbose",
    ]


@pytest.mark.parametrize("help_option", ["-h", "--help"])
def test_tool_exec_command_dash_help_missing_params(help_option):
    """Execute a command (which needs params) asking for help."""

    def fill_parser(self, parser):  # pylint: disable=unused-argument
        parser.add_argument("mandatory")

    cmd = create_command("somecommand", "This command does that.")
    cmd.fill_parser = fill_parser
    command_groups = [CommandGroup("group", [cmd])]
    dispatcher = Dispatcher("testapp", command_groups)

    with patch("craft_cli.helptexts.HelpBuilder.get_command_help") as mock:
        mock.return_value = "test help"
        with pytest.raises(ProvideHelpException) as exc_cm:
            dispatcher.pre_parse_args(["somecommand", help_option])

    # check the result of the full help builder is what is transmitted
    assert str(exc_cm.value) == "test help"

    # check the given information to the help text builder
    args = mock.call_args[0]
    assert args[0].__class__ == cmd
    assert sorted(x[0] for x in args[1]) == [
        "-h, --help",
        "-q, --quiet",
        "-t, --trace",
        "-v, --verbose",
        "mandatory",
    ]


def test_tool_exec_command_wrong_option():
    """Execute a correct command but with a wrong option."""
    cmd = create_command("somecommand", "This command does that.")
    command_groups = [CommandGroup("group", [cmd])]
    dispatcher = Dispatcher("testapp", command_groups, summary="general summary")
    dispatcher.pre_parse_args(["somecommand", "--whatever"])

    with pytest.raises(ArgumentParsingError) as exc_cm:
        dispatcher.load_command("config")

    expected = textwrap.dedent(
        """\
        Usage: testapp [options] command [args]...
        Try 'testapp somecommand -h' for help.

        Error: unrecognized arguments: --whatever
        """
    )

    error = exc_cm.value
    assert str(error) == expected


def test_tool_exec_command_bad_option_type():
    """Execute a correct command but giving the valid option a bad value."""

    def fill_parser(self, parser):  # pylint: disable=unused-argument
        parser.add_argument("--number", type=int)

    cmd = create_command("somecommand", "This command does that.")
    cmd.fill_parser = fill_parser

    command_groups = [CommandGroup("group", [cmd])]
    dispatcher = Dispatcher("testapp", command_groups, summary="general summary")
    dispatcher.pre_parse_args(["somecommand", "--number=foo"])

    with pytest.raises(ArgumentParsingError) as exc_cm:
        dispatcher.load_command("config")

    expected = textwrap.dedent(
        """\
        Usage: testapp [options] command [args]...
        Try 'testapp somecommand -h' for help.

        Error: argument --number: invalid int value: 'foo'
        """
    )

    error = exc_cm.value
    assert str(error) == expected


def test_tool_exec_help_command_on_command_ok():
    """Execute the app asking for help on a command ok."""
    cmd = create_command("somecommand", "This command does that.")
    command_groups = [CommandGroup("group", [cmd])]
    dispatcher = Dispatcher("testapp", command_groups)

    with patch("craft_cli.helptexts.HelpBuilder.get_command_help") as mock:
        mock.return_value = "test help"
        with pytest.raises(ProvideHelpException) as exc_cm:
            dispatcher.pre_parse_args(["help", "somecommand"])

    # check the result of the help builder is what is transmitted
    assert str(exc_cm.value) == "test help"

    # check the given information to the help text builder
    args = mock.call_args[0]
    assert isinstance(args[0], cmd)
    assert sorted(x[0] for x in args[1]) == [
        "-h, --help",
        "-q, --quiet",
        "-t, --trace",
        "-v, --verbose",
    ]


def test_tool_exec_help_command_on_command_complex():
    """Execute the app asking for help on a command with parameters and options."""

    def fill_parser(self, parser):  # pylint: disable=unused-argument
        parser.add_argument("param1", help="help on param1")
        parser.add_argument("param2", help="help on param2")
        parser.add_argument("param3", metavar="transformed3", help="help on param2")
        parser.add_argument("--option1", help="help on option1")
        parser.add_argument("-o2", "--option2", help="help on option2")
        parser.add_argument("--option3", nargs=2, metavar=("ot1", "ot2"), help="help on option3")

    cmd = create_command("somecommand", "This command does that.")
    cmd.fill_parser = fill_parser
    command_groups = [CommandGroup("group", [cmd])]
    dispatcher = Dispatcher("testapp", command_groups)

    with patch("craft_cli.helptexts.HelpBuilder.get_command_help") as mock:
        mock.return_value = "test help"
        with pytest.raises(ProvideHelpException) as exc_cm:
            dispatcher.pre_parse_args(["help", "somecommand"])

    # check the result of the help builder is what is transmitted
    assert str(exc_cm.value) == "test help"

    # check the given information to the help text builder
    args = mock.call_args[0]
    assert args[0].__class__ == cmd
    expected_options = [
        ("--option1", "help on option1"),
        ("--option3", "help on option3"),
        ("-h, --help", "Show this help message and exit"),
        ("-o2, --option2", "help on option2"),
        ("-q, --quiet", "Only show warnings and errors, not progress"),
        ("-t, --trace", "Show all information needed to trace internal behaviour"),
        ("-v, --verbose", "Show debug information and be more verbose"),
        ("param1", "help on param1"),
        ("param2", "help on param2"),
        ("transformed3", "help on param2"),
    ]
    assert sorted(args[1]) == expected_options


def test_tool_exec_help_command_on_command_no_help():
    """Execute the app asking for help on a command with an options and params without help."""

    def fill_parser(self, parser):  # pylint: disable=unused-argument
        parser.add_argument("param")
        parser.add_argument("--option")

    cmd = create_command("somecommand", "This command does that.")
    cmd.fill_parser = fill_parser
    command_groups = [CommandGroup("group", [cmd])]
    dispatcher = Dispatcher("testapp", command_groups)

    with patch("craft_cli.helptexts.HelpBuilder.get_command_help") as mock:
        mock.return_value = "test help"
        with pytest.raises(ProvideHelpException) as exc_cm:
            dispatcher.pre_parse_args(["help", "somecommand"])

    # check the result of the help builder is what is transmitted
    assert str(exc_cm.value) == "test help"

    # check the given information to the help text builder
    args = mock.call_args[0]
    assert args[0].__class__ == cmd
    expected_options = [
        ("--option", ""),
        ("-h, --help", "Show this help message and exit"),
        ("-q, --quiet", "Only show warnings and errors, not progress"),
        ("-t, --trace", "Show all information needed to trace internal behaviour"),
        ("-v, --verbose", "Show debug information and be more verbose"),
        ("param", ""),
    ]
    assert sorted(args[1]) == expected_options


def test_tool_exec_help_command_on_command_wrong():
    """Execute the app asking for help on a command which does not exist."""
    command_groups = [CommandGroup("group", [])]
    dispatcher = Dispatcher("testapp", command_groups)

    with patch("craft_cli.helptexts.HelpBuilder.get_usage_message") as mock:
        mock.return_value = "test help"
        with pytest.raises(ArgumentParsingError) as exc_cm:
            dispatcher.pre_parse_args(["help", "wrongcommand"])
    error = exc_cm.value

    # check the given information to the help text builder
    assert mock.call_args[0] == ("command 'wrongcommand' not found to provide help for",)

    # check the result of the help builder is what is shown
    assert str(error) == "test help"


def test_tool_exec_help_command_all():
    """Execute the app asking for detailed help."""
    command_groups = [CommandGroup("group", [])]
    dispatcher = Dispatcher("testapp", command_groups)

    with patch("craft_cli.helptexts.HelpBuilder.get_detailed_help") as mock:
        mock.return_value = "test help"
        with pytest.raises(ProvideHelpException) as exc_cm:
            dispatcher.pre_parse_args(["help", "--all"])

    # check the result of the help builder is what is transmitted
    assert str(exc_cm.value) == "test help"

    # check the given information to the help text builder
    args = mock.call_args[0]
    assert sorted(x[0] for x in args[0]) == [
        "-h, --help",
        "-q, --quiet",
        "-t, --trace",
        "-v, --verbose",
    ]
