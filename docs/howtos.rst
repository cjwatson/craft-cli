*******
HOW TOs
*******

.. _howto_other_logfile:

Use a different logfile structure than the default
==================================================

To override :ref:`the default management of application log files <expl_log_management>`, a file path can be specified when initiating the `emit` object, using the ``log_filepath`` parameter::

    emit.init(mode, appname, greeting, log_filepath)

Note that if you use this option, is up to you to provide proper management of those files (e.g. to rotate them).


.. _howto_return_codes:

End the application with different return codes
===============================================

To enable the application to return different return codes in different situations, you need wrap the Dispatcher in a specific way (having different return codes in the different situations), to take in consideration the returned value from the command's run, and of course make the application to actually return the specific value.

In the following code structure we see all these effects at once::

    try:
        ...
        retcode = dispatcher.run()
        if retcode is None:
            retcode = 0
    except ArgumentParsingError as err:
        print(err, file=sys.stderr)  # to stderr, as argparse normally does
        emit.ended_ok()
        retcode = 1
    except ProvideHelpException as err:
        print(err, file=sys.stderr)  # to stderr, as argparse normally does
        emit.ended_ok()
        retcode = 0
    except CraftError as err:
        emit.error(err)
        retcode = err.retcode
    except KeyboardInterrupt as exc:
        error = CraftError("Interrupted.")
        error.__cause__ = exc
        emit.error(error)
        retcode = 1
    except Exception as exc:
        error = CraftError(f"Application internal error: {exc!r}")
        error.__cause__ = exc
        emit.error(error)
        retcode = 1
    else:
        emit.ended_ok()
    sys.exit(retcode)

In detail:

- the return code from the command's execution is bound when calling `dispatcher.run`, supporting the case of it not returning anything (defaults to `0`)

- have different return codes assigned for the different `except` situations, with two particular cases: for ``ProvideHelpException`` it's `0` as it's a normal exit situation when the user requested for help, and for ``CraftError`` where the return code is taken from the exception itself

- a `sys.exit` at the very end for the process to return the value


Raise more informational errors
===============================

To provide more information to the user in case of an error, you can use the ``CraftError`` exception provided by the ``craft-cli`` library.

So, in addition of just passing a message to the user...

::

    raise CraftError("The indicated file does not exist.")

...you can provide more information:

- ``details``: full error details received from a third party or extended information about the situation, useful for debugging but not to be normally shown to the user. E.g.::

    raise CraftError(
        "Cannot access the indicated file.", 
        details=f"File permissions: {oct(filepath.stat().st_mode)}")

    raise CraftError(
        f"Server returned bad code {error_code}",
        details=f"Full server response: {response.content!r}")
    

- ``resolution``: an extra line indicating to the user how the error may be fixed or avoided. E.g.::

    raise CraftError(
        "Cannot remove the directory.",
        resolution="Confirm that the directory is empty and has proper permissions.")

- ``docs_url``: an URL to point the user to documentation. E.g.::

    raise CraftError(
        "Invalid configuration: bad version value.",
        docs_url="https://mystuff.com/docs/how-to-migrate-config")

- ``reportable``: if an error report should be sent to some error-handling backend (like Sentry). E.g.::

    raise CraftError(
        f"Unexpected subprocess return code: {proc.returncode}.",
        reportable=True)

- ``retcode``: the code to return when the application finishes (see :ref:`how to use this when wrapping Dispatcher <howto_return_codes>`)

You should use any combination of these, as looks appropriate.

For further information reported to the user and/or sent to the log file, you should create ``CraftError`` specifying the original exception (if any). E.g.::

    try:
        ...
    except IOError as exc:
        raise CraftError(f"Error when frunging the perculux: {exc}") from exc

Finally, if you want to build a hierarchy of errors in the application, you should start the tree inheriting ``CraftError`` to use this functionality.


.. _howto_global_args:

Define and use other global arguments
=====================================

To define more automatic global arguments than the ones provided automatically by ``Dispatcher`` (see :ref:`this explanation <expl_global_args>` for more information), use the ``GlobalArgument`` object to create all you need and pass them to the ``Dispatcher`` at instatiaton time.

Check `its reference <craft_cli.dispatcher.html#craft_cli.dispatcher.GlobalArgument>`_ for more information about the parameters needed, but it's very straightforward to create these objects. E.g.::

    ga_sec = GlobalArgument("secure_mode", "flag", "-s", "--secure", "Run the app in secure mode")
    
To use it, just pass a list of the needed global arguments to the dispatcher using the ``extra_global_args`` option::

    dispatcher = Dispatcher(..., extra_global_args=[ga_sec])

The ``dispatcher.pre_parse_args`` method returns the global arguments already parsed, as a dictionary. Use the name you gave to the global argument to check for its value and react properly. E.g.::

    global_args = dispatcher.pre_parse_args(sys.argv[1:])
    app_config.set_secure_mode(global_args["secure_mode"])


Set a default command in the application
========================================

To allow the application to run a command if none was given in the command line, you need to set a default command in the application when instantiating `Dispatcher <craft_cli.dispatcher.html#craft_cli.dispatcher.Dispatcher>`_::

    dispatcher = Dispatcher(..., default_command=MyImportantCommand)

This way ``craft-cli`` will run the specified command if none was given, e.g.::

    $ my-super-app

And even run the specified default command if options are given for that command::

    $ my-super-app --important-option
