const child_process = require('child_process');
const path = require('path');

const helpers = require('./helpers');
const test = require('tape');

const decodeB64 = helpers.decodeB64;

const args = process.argv.slice();
const nodePath = path.resolve(args[0], '..');
const envPath = `${path.resolve(__dirname, 'shims')}:${nodePath}`;
const cloneScriptPath = path.resolve(__dirname, '../clone.sh');

const BRANCH = 'fake-branch';
const OWNER = 'fake-user';
const REPOSITORY = 'cool-things';
const SOURCE_OWNER = '18f';
const SOURCE_REPO = 'test-repo';

const expectedRmArguments = [ '-rf', '_site' ];

function execCloneScript(opts) {
  const output = child_process.execSync(cloneScriptPath, opts).toString();
  const commands = output.split('\n').reduce(function(result, current) {
    const decoded = decodeB64(current);
    if (decoded !== '') {
      result.push(JSON.parse(decoded).slice(2));
    }

    return result;
  }, []);

  return commands;
}

test('executes clone command without SOURCE_OWNER or SOURCE_REPO', (t) => {
  const opts = {
    env: {
      BRANCH,
      OWNER,
      REPOSITORY,
      PATH: envPath
    }
  };
  // const output = child_process.execSync(cloneScriptPath, opts).toString();
  // const decoded = decodeB64(output);
  // console.log('decoded', decoded);
  // const command = JSON.parse(decoded).slice(2);

  const commands = execCloneScript(opts);
  console.log('commands', commands);

  const expectedCloneArguments = [
    'clone',
    '-b',
    BRANCH,
    '--single-branch',
    `https://@github.com/${OWNER}/${REPOSITORY}.git`,
    '.'
  ];

  t.plan(2);
  t.deepEqual(commands[0], expectedCloneArguments);
  t.deepEqual(commands[1], expectedRmArguments);
});

test('executes clone command with SOURCE_OWNER or SOURCE_REPO', (t) => {
  const opts = {
    env: {
      BRANCH,
      OWNER,
      REPOSITORY,
      SOURCE_OWNER,
      SOURCE_REPO,
      PATH: envPath
    }
  };

  const commands = execCloneScript(opts);
  console.log('commands', commands);

  const expectedCloneArguments = [
    'clone',
    '-b',
    BRANCH,
    '--single-branch',
    `https://@github.com/${SOURCE_OWNER}/${SOURCE_REPO}.git`,
    '.'
  ];
  const expectedRemoteAddArguemnts = [
    'remote',
    'add',
    'destination',
    `https://@github.com/${OWNER}/${REPOSITORY}.git`
  ];
  const expectedPushCommands = [
    'push',
    'destination',
    BRANCH
  ];

  t.plan(5);
  t.equal(commands.length, 4);
  t.deepEqual(commands[0], expectedCloneArguments);
  t.deepEqual(commands[1], expectedRemoteAddArguemnts);
  t.deepEqual(commands[2], expectedPushCommands);
  t.deepEqual(commands[3], expectedRmArguments);
});