
### Notes

- http://docs.pyinvoke.org/en/latest/
- use `env` kwarg to `ctx.run` to specify the environment for a command.
  - This will be good for making sure sub-commands don't have access to privileged info!!!
- ???: Once we have all these little tasks described,
  how do they get called in order, error-handled, etc?
- TODO: gemnasium, circle, etc.
- TODO: dockerize for both dev and deploy
- TODO: make sure all ctx.run is called with env={} or with applicable env ONLY
- IDEA: What about having _very_ discrete bash scripts for doing stuff like setting up ruby, setting up node, etc? Would cut down on the context manager code, and I think it would help with clarity. They could even be "inlined." Not sure about the balance to strike yet...

For dev, use `docker-compose run app bash` to start up a transient `app` container.

### System-level dependencies

1. `git`
1. `python 3.6`
1. `nvm`
1. `ruby` # TODO: version?
