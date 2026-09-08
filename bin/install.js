#!/usr/bin/env node
// SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
// SPDX-License-Identifier: Apache-2.0



const fs = require('fs');
const path = require('path');
const readline = require('readline');

const USAGE = `Usage: hermes-nemo-skills [options]

Install the curated Hermes skill bundle into an agent skill directory.

Options:
  --target, -t <dir>   Skill root directory to install into (see resolution order below)
  --group, -g <name>   Install only the named top-level group (repeatable; e.g. operations)
  --skill, -s <name>   Install only the named skill directory (repeatable; matched anywhere in the tree)
  --list, -l           List available groups and skill counts, then exit
  --force, -f          Overwrite existing files (default: skip and report)
  --dry-run            Print what would be copied without writing anything
  --help, -h           Show this help

Target resolution order:
  1. --target <dir>
  2. $HERMES_SKILLS_DIR
  3. $HERMES_HOME/skills
  4. interactive prompt (requires a TTY)

The target is the skill root: the directory whose direct children are the
installed groups (agent-platform/, operations/, integrations/, workflows/).
Selections compose: --group operations --skill slack-channel-finder installs
the operations group plus that integrations skill. Groups are copied as whole
directories; per-skill LICENSE files travel with their skills. Every copied
SKILL.md is checked for a Markdown title or frontmatter, matching
scripts/validate-skills.sh.
`;

const GROUP_EXCLUDES = new Set(['licenses']);
const SKILL_FILE = 'SKILL.md';

function fail(message, code = 1) {
  console.error(`error: ${message}`);
  process.exit(code);
}

function parseArgs(argv) {
  const opts = {
    target: null,
    groups: [],
    skills: [],
    list: false,
    force: false,
    dryRun: false,
    help: false,
  };
  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    const value = () => {
      const v = argv[++i];
      if (v === undefined) fail(`missing value for ${arg}`);
      return v;
    };
    switch (arg) {
      case '--target': case '-t': opts.target = value(); break;
      case '--group': case '-g': opts.groups.push(value()); break;
      case '--skill': case '-s': opts.skills.push(value()); break;
      case '--list': case '-l': opts.list = true; break;
      case '--force': case '-f': opts.force = true; break;
      case '--dry-run': opts.dryRun = true; break;
      case '--help': case '-h': opts.help = true; break;
      default:
        console.error(`unknown option: ${arg}\n`);
        opts.help = true;
        process.exitCode = 2;
    }
  }
  return opts;
}

function repoRoot() {
  // bin/install.js lives one level below the package root; works for npx
  // installs, npm -g installs, and running from a repository clone.
  return path.resolve(__dirname, '..');
}

function listGroups(skillsRoot) {
  return fs.readdirSync(skillsRoot, { withFileTypes: true })
    .filter((e) => e.isDirectory() && !GROUP_EXCLUDES.has(e.name))
    .map((e) => e.name)
    .sort();
}

function walkFiles(root, rel = '') {
  const out = [];
  for (const entry of fs.readdirSync(root, { withFileTypes: true })) {
    const relPath = rel ? `${rel}/${entry.name}` : entry.name;
    if (entry.isDirectory()) {
      out.push(...walkFiles(path.join(root, entry.name), relPath));
    } else if (entry.isFile()) {
      out.push(relPath);
    }
  }
  return out;
}

function isSkillMd(relPath) {
  return relPath === SKILL_FILE || relPath.endsWith(`/${SKILL_FILE}`);
}

function countSkills(skillsRoot, group) {
  return walkFiles(path.join(skillsRoot, group)).filter(isSkillMd).length;
}

function findSkillDirs(skillsRoot, groups, name) {
  const hits = [];
  for (const group of groups) {
    const groupDir = path.join(skillsRoot, group);
    const stack = [''];
    while (stack.length) {
      const rel = stack.pop();
      const abs = path.join(groupDir, rel);
      for (const entry of fs.readdirSync(abs, { withFileTypes: true })) {
        if (!entry.isDirectory()) continue;
        const childRel = rel ? `${rel}/${entry.name}` : entry.name;
        if (entry.name === name && fs.existsSync(path.join(abs, entry.name, SKILL_FILE))) {
          hits.push({ group, rel: childRel });
        } else {
          stack.push(childRel);
        }
      }
    }
  }
  return hits;
}

async function resolveTarget(opts) {
  if (opts.target) return opts.target;
  if (process.env.HERMES_SKILLS_DIR) return process.env.HERMES_SKILLS_DIR;
  if (process.env.HERMES_HOME) return path.join(process.env.HERMES_HOME, 'skills');
  if (process.stdout.isTTY && process.stdin.isTTY) {
    const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
    const answer = await new Promise((resolve) => {
      rl.question('Install into skill root directory (e.g. ~/.hermes/skills): ', resolve);
    });
    rl.close();
    const trimmed = (answer || '').trim();
    if (!trimmed) fail('no target given; rerun with --target <dir>');
    return trimmed;
  }
  fail('no target given (not a TTY); rerun with --target <dir>');
  return null;
}

function copyTree(src, dest, opts) {
  const stats = { files: 0, skills: 0, skipped: 0, failed: [] };
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      const sub = copyTree(srcPath, destPath, opts);
      stats.files += sub.files;
      stats.skills += sub.skills;
      stats.skipped += sub.skipped;
      stats.failed.push(...sub.failed);
    } else if (entry.isFile()) {
      if (fs.existsSync(destPath) && !opts.force) {
        stats.skipped += 1;
        continue;
      }
      stats.files += 1;
      if (entry.name === SKILL_FILE) stats.skills += 1;
      if (!opts.dryRun) {
        try {
          fs.copyFileSync(srcPath, destPath);
        } catch (err) {
          stats.failed.push(`${path.relative(process.cwd(), destPath)}: ${err.message}`);
        }
      }
    }
  }
  return stats;
}

function validateSkillFile(absPath) {
  const content = fs.readFileSync(absPath, 'utf8');
  return /(^# |^---$)/m.test(content);
}

async function main() {
  const opts = parseArgs(process.argv.slice(2));
  if (opts.help) {
    console.log(USAGE);
    return process.exitCode;
  }

  const root = repoRoot();
  const skillsRoot = path.join(root, 'skills');
  if (!fs.existsSync(skillsRoot)) fail(`skills tree not found at ${skillsRoot}`);

  const groups = listGroups(skillsRoot);
  if (opts.list) {
    let total = 0;
    for (const group of groups) {
      const n = countSkills(skillsRoot, group);
      total += n;
      console.log(`${group.padEnd(16)} ${String(n).padStart(3)} skills`);
    }
    console.log(`${'total'.padEnd(16)} ${String(total).padStart(3)} skills`);
    return 0;
  }

  // Selected groups: the ones explicitly named, or all of them by default.
  const selectedGroups = [];
  if (opts.groups.length) {
    for (const g of opts.groups) {
      if (!groups.includes(g)) {
        fail(`unknown group '${g}'; available groups: ${groups.join(', ')}`, 2);
      }
      if (!selectedGroups.includes(g)) selectedGroups.push(g);
    }
  } else {
    selectedGroups.push(...groups);
  }

  // Selections: whole groups plus (or, if only --skill was given, only) named
  // skills. --skill always searches all groups, so combinations compose.
  const onlySkills = opts.skills.length > 0 && opts.groups.length === 0;
  const selections = [];
  const seen = new Set();
  if (!onlySkills) {
    for (const g of selectedGroups) {
      selections.push({ label: g, src: path.join(skillsRoot, g), rel: g });
      seen.add(g);
    }
  }
  for (const name of opts.skills) {
    const hits = findSkillDirs(skillsRoot, groups, name);
    if (!hits.length) {
      fail(`no skill named '${name}' found in any group (${groups.join(', ')})`, 2);
    }
    for (const hit of hits) {
      const key = `${hit.group}/${hit.rel}`;
      if (seen.has(key)) continue;
      seen.add(key);
      selections.push({ label: key, src: path.join(skillsRoot, hit.group, hit.rel), rel: key });
    }
  }

  const target = await resolveTarget(opts);
  const totals = { files: 0, skills: 0, skipped: 0, failed: [] };
  const installedSkillFiles = [];
  for (const sel of selections) {
    const dest = path.join(target, sel.rel);
    const stats = copyTree(sel.src, dest, opts);
    totals.files += stats.files;
    totals.skills += stats.skills;
    totals.skipped += stats.skipped;
    totals.failed.push(...stats.failed);
    if (!opts.dryRun) {
      for (const file of walkFiles(dest)) {
        if (isSkillMd(file)) installedSkillFiles.push(path.join(dest, file));
      }
    }
    console.log(
      `${opts.dryRun ? 'would install' : 'installed'} ${sel.label} -> ${dest} ` +
      `(${stats.files} file(s), ${stats.skills} skill(s)` +
      `${stats.skipped ? `, ${stats.skipped} skipped` : ''})`,
    );
  }

  let invalid = 0;
  for (const file of installedSkillFiles) {
    if (!validateSkillFile(file)) {
      invalid += 1;
      console.error(`missing Markdown title: ${file}`);
    }
  }
  if (invalid > 0) fail(`${invalid} installed SKILL.md file(s) failed validation`);

  console.log(
    `done${opts.dryRun ? ' (dry run)' : ''}: ${totals.files} file(s), ${totals.skills} skill(s) ` +
      `installed to ${target}` +
      `${totals.skipped ? `, ${totals.skipped} skipped (use --force to overwrite)` : ''}`,
  );
  if (totals.failed.length > 0) {
    console.error(`${totals.failed.length} file(s) could not be written:`);
    for (const f of totals.failed) console.error(`  ${f}`);
    return 1;
  }
  return 0;
}

main()
  .then((code) => process.exit(code ?? process.exitCode ?? 0))
  .catch((err) => fail(err.message));
