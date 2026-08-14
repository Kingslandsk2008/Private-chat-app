(function() {
'use strict';

window.KAJUU_TOOLS = {
  call: async function(tool, params) {
    try {
      const resp = await fetch('/api/tools/call', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ tool, params }),
      });
      return await resp.json();
    } catch (e) {
      return { error: e.message, status: 'error' };
    }
  },

  callParallel: async function(calls) {
    try {
      const resp = await fetch('/api/tools/parallel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ calls }),
      });
      return await resp.json();
    } catch (e) {
      return { error: e.message, status: 'error' };
    }
  },

  listTools: async function() {
    const resp = await fetch('/api/tools');
    return await resp.json();
  },

  searchTools: async function(query) {
    try {
      const resp = await fetch('/api/tools/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      });
      return await resp.json();
    } catch (e) {
      return { error: e.message };
    }
  },

  // Agent operations
  agent: {
    spawn: async function(task, role) {
      const resp = await fetch('/api/agent/spawn', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task, role }),
      });
      return await resp.json();
    },
    wait: async function(agentId, timeout) {
      const resp = await fetch(`/api/agent/${agentId}/wait?timeout=${timeout || 60}`);
      return await resp.json();
    },
    result: async function(agentId) {
      const resp = await fetch(`/api/agent/${agentId}/result`);
      return await resp.json();
    },
    close: async function(agentId) {
      const resp = await fetch(`/api/agent/${agentId}`, { method: 'DELETE' });
      return await resp.json();
    },
    list: async function() {
      const resp = await fetch('/api/agents');
      return await resp.json();
    },
  },

  // Filesystem
  fs: {
    read: function(path, offset, limit) {
      return window.KAJUU_TOOLS.call('read', { path, offset, limit });
    },
    write: function(path, content) {
      return window.KAJUU_TOOLS.call('write', { path, content });
    },
    edit: function(path, oldString, newString) {
      return window.KAJUU_TOOLS.call('edit', { path, old_string: oldString, new_string: newString });
    },
    glob: function(pattern, path) {
      return window.KAJUU_TOOLS.call('glob', { pattern, path });
    },
    grep: function(pattern, include, path) {
      return window.KAJUU_TOOLS.call('grep', { pattern, include, path });
    },
    listDir: function(path) {
      return window.KAJUU_TOOLS.call('list_dir', { path });
    },
    delete: function(path, recursive) {
      return window.KAJUU_TOOLS.call('delete_file', { path, recursive });
    },
    info: function(path) {
      return window.KAJUU_TOOLS.call('file_info', { path });
    },
  },

  // Shell
  shell: {
    bash: function(command, workdir, timeout) {
      return window.KAJUU_TOOLS.call('bash', { command, workdir, timeout });
    },
    python: function(code, timeout) {
      return window.KAJUU_TOOLS.call('python', { code, timeout });
    },
  },

  // Web
  web: {
    fetch: function(url, format, timeout) {
      return window.KAJUU_TOOLS.call('web_fetch', { url, format, timeout });
    },
    search: function(query, numResults) {
      return window.KAJUU_TOOLS.call('web_search', { query, num_results: numResults });
    },
    imageSearch: function(query, count) {
      return window.KAJUU_TOOLS.call('image_search', { query, count });
    },
  },

  // Git
  git: {
    status: function(path) {
      return window.KAJUU_TOOLS.call('git_status', { path });
    },
    diff: function(path, staged) {
      return window.KAJUU_TOOLS.call('git_diff', { path, staged });
    },
    log: function(path, count) {
      return window.KAJUU_TOOLS.call('git_log', { path, count });
    },
    commit: function(message, files, path) {
      return window.KAJUU_TOOLS.call('git_commit', { message, files, path });
    },
    branch: function(action, name, path) {
      return window.KAJUU_TOOLS.call('git_branch', { action, name, path });
    },
  },

  // Memory
  memory: {
    list: function() {
      return fetch('/api/memory').then(r => r.json());
    },
    write: function(name, content, mode) {
      return fetch('/api/memory', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, content, mode: mode || 'write' }),
      }).then(r => r.json());
    },
    read: function(name) {
      return fetch(`/api/memory/${name}`).then(r => r.json());
    },
    delete: function(name) {
      return fetch(`/api/memory/${name}`, { method: 'DELETE' }).then(r => r.json());
    },
    search: function(query) {
      return fetch('/api/memory/search', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query }),
      }).then(r => r.json());
    },
  },

  // Skills
  skills: {
    list: function() {
      return fetch('/api/skills').then(r => r.json());
    },
    load: function(name) {
      return fetch(`/api/skills/${name}`).then(r => r.json());
    },
    create: function(name, description, prompt) {
      return fetch('/api/skills', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name, description, prompt }),
      }).then(r => r.json());
    },
    delete: function(name) {
      return fetch(`/api/skills/${name}`, { method: 'DELETE' }).then(r => r.json());
    },
  },

  // GitHub
  github: {
    issueList: function(repo, state, limit) {
      return window.KAJUU_TOOLS.call('gh_issue_list', { repo, state, limit });
    },
    issueCreate: function(repo, title, body) {
      return window.KAJUU_TOOLS.call('gh_issue_create', { repo, title, body });
    },
    prList: function(repo) {
      return window.KAJUU_TOOLS.call('gh_pr_list', { repo });
    },
    searchCode: function(query) {
      return window.KAJUU_TOOLS.call('gh_search_code', { query });
    },
    repoInfo: function(repo) {
      return window.KAJUU_TOOLS.call('gh_repo_info', { repo });
    },
    fileContent: function(repo, path, ref) {
      return window.KAJUU_TOOLS.call('gh_file_content', { repo, path, ref });
    },
  },
};

})();
