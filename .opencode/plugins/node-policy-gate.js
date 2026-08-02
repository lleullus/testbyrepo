'use strict';

const fs = require('node:fs');
const path = require('node:path');
const { admitChange } = require('../../adapter/node/src');

const SAFE_TOOLS = new Set([
  'glob',
  'grep',
  'list',
  'lsp',
  'question',
  'read',
  'skill',
  'todowrite',
  'webfetch',
  'websearch'
]);
const POLICY_TOOLS = new Set(['node_policy_admit', 'node_policy_write']);

async function NodePolicyGatePlugin({ directory, worktree }) {
  const repositoryRoot = fs.realpathSync(worktree || directory);
  const requestStates = new Map();
  const admissions = new Map();

  return {
    tool: {
      node_policy_admit: {
        description: 'Run mandatory Node/TypeScript change admission for the current user request before any file mutation.',
        args: {
          projectDirectory: {
            type: 'string',
            description: 'Node/TypeScript project directory inside the current worktree.'
          }
        },
        async execute(args, context) {
          const requestState = requestStates.get(context.sessionID);
          if (!requestState || !requestState.request) {
            throw new Error('No authoritative user request is bound to this session.');
          }
          const projectDirectory = requireContainedProject(repositoryRoot, args.projectDirectory);
          const session = admitChange({ projectDirectory, request: requestState.request });
          requestState.awaitingClarification = session.verdict === 'INCONCLUSIVE' && session.questions.length > 0;
          admissions.set(context.sessionID, { projectDirectory, request: requestState.request, session });
          return JSON.stringify({
            verdict: session.verdict,
            summary: session.summary,
            questions: session.questions,
            details: session.details
          }, null, 2);
        }
      },
      node_policy_write: {
        description: 'Apply declarative file writes through the current PASS admission. Ordinary edit, patch, shell, and task mutation paths are blocked.',
        args: {
          writes: {
            type: 'array',
            minItems: 1,
            items: {
              type: 'object',
              properties: {
                path: { type: 'string' },
                content: { type: 'string' }
              },
              required: ['path', 'content'],
              additionalProperties: false
            }
          }
        },
        async execute(args, context) {
          const current = admissions.get(context.sessionID);
          const requestState = requestStates.get(context.sessionID);
          if (!current || !requestState || requestState.request !== current.request) {
            throw new Error('No current admission exists for this user request.');
          }
          const result = current.session.attemptWrite({ request: requestState.request, writes: args.writes });
          return JSON.stringify(result, null, 2);
        }
      }
    },
    async 'chat.message'(input, output) {
      const request = output.parts
        .filter((part) => part && part.type === 'text' && typeof part.text === 'string')
        .map((part) => part.text.trim())
        .filter(Boolean)
        .join('\n');
      const previous = requestStates.get(input.sessionID);
      requestStates.set(input.sessionID, {
        awaitingClarification: false,
        request: previous && previous.awaitingClarification
          ? `${previous.request}\n${request}`
          : request
      });
      admissions.delete(input.sessionID);
    },
    async 'tool.execute.before'(input) {
      const toolName = normalizeToolName(input.tool);
      if (POLICY_TOOLS.has(toolName) || SAFE_TOOLS.has(toolName)) {
        return;
      }
      throw new Error(
        `Node policy gate blocked tool "${input.tool}". Use node_policy_admit, then node_policy_write for admitted file mutations.`
      );
    }
  };
}

function requireContainedProject(repositoryRoot, projectDirectory) {
  if (typeof projectDirectory !== 'string' || projectDirectory.length === 0) {
    throw new Error('projectDirectory is required.');
  }
  const resolved = fs.realpathSync(path.resolve(repositoryRoot, projectDirectory));
  const relative = path.relative(repositoryRoot, resolved);
  if (relative === '..' || relative.startsWith(`..${path.sep}`) || path.isAbsolute(relative)) {
    throw new Error('projectDirectory must stay inside the current worktree.');
  }
  return resolved;
}

function normalizeToolName(toolName) {
  return typeof toolName === 'string' ? toolName : '';
}

module.exports = NodePolicyGatePlugin;
module.exports.NodePolicyGatePlugin = NodePolicyGatePlugin;
