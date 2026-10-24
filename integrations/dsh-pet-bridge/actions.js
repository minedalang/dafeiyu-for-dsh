// DSH owns perception/decision; DaFeiYu owns rendering and autonomous life.
// Both tools are local-only, zero-dependency, allowlisted. No screen capture.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { submitPetAction } from './index.js';

export const name = 'dsh-pet-actions';
export const inject = ['tools'];

function petBridgeDir() {
  if (process.platform === 'win32') return path.join(process.env.APPDATA || os.homedir(), 'dsh-pet-bridge');
  if (process.platform === 'darwin') return path.join(os.homedir(), 'Library', 'Application Support', 'dsh-pet-bridge');
  return path.join(os.homedir(), '.config', 'dsh-pet-bridge');
}

export function loadPetAnimations() {
  const file = path.join(petBridgeDir(), 'pet-animations.json');
  let parsed;
  try { parsed = JSON.parse(fs.readFileSync(file, 'utf8')); }
  catch { return JSON.stringify({ ready: false, message: '桌宠素材清单尚未就绪；请运行 v8.2 大肥鱼并打开 DSH 联动，确认角色已加载。' }); }
  if (parsed?.schema !== 1 || !Array.isArray(parsed.animations)) {
    return JSON.stringify({ ready: false, message: '桌宠素材清单格式错误，请升级桌宠端。' });
  }
  const animations = parsed.animations.filter(s => typeof s === 'string' && s.length <= 120).slice(0, 256);
  return JSON.stringify({ ready: true, animations, idles: Array.isArray(parsed.idles) ? parsed.idles.slice(0, 32) : [],
    note: '只可向 pet_action.animation 填写这里的精确动画名称；这不是浏览器或电脑控制工具。' });
}

export function apply(ctx) {
  ctx.tools.register({
    name: 'pet_animations',
    description: 'Query the local DaFeiYu pet\'s ACTUAL available animation names before asking it to play a specific clip. Read-only. No API or browser access. If ready=false, do not invent an animation name.',
    parameters: { type: 'object', properties: {}, additionalProperties: false },
    output: { schema: { type: 'string' }, render: (_args, value) => [{ type: 'text', text: value }] },
    async execute() { return loadPetAnimations(); },
  });
  ctx.tools.register({
    name: 'pet_action',
    description: 'You are the observer AND decision-maker for DaFeiYu while you work. After YOU have actually read relevant video subtitles, page contents or visual frames, optionally react in the pet\'s playful Chinese persona using a concise expressive animation and/or speech. Only react when something meaningful happens; silence is valid. Never claim to have seen unheard/unread content. Use pet_animations first if specifying animation. This tool requests local pet rendering only; it never operates the browser, mouse or files. DSH-active periods temporarily yield autonomous activity to your tool actions; user interaction and alerts still win.',
    parameters: {
      type: 'object',
      properties: {
        mood: { type: 'string', enum: ['search', 'watch', 'think', 'happy', 'work', 'idle'], description: 'Legacy semantic mood / fallback when no exact animation requested' },
        animation: { type: 'string', maxLength: 120, description: 'Optional EXACT animation name returned by pet_animations. No paths, URLs or invented names.' },
        speech: { type: 'string', maxLength: 90, description: 'Optional short Chinese pet speech, not a transcript, URL, secret, or raw webpage content' },
        duration_seconds: { type: 'integer', minimum: 3, maximum: 30, description: 'How long to give this DSH-directed reaction priority (NOT repeated playback of a one-shot clip)' },
        priority: { type: 'string', enum: ['ambient', 'normal', 'urgent'], description: 'ambient=do not interrupt a continuing activity; normal=yield non-sleep activities; urgent=may wake sleeping pet. Use urgent sparingly.' },
      },
      required: ['mood'],
      additionalProperties: false,
    },
    output: { schema: { type: 'string' }, render: (_args, value) => [{ type: 'text', text: value }] },
    async execute(args) {
      if (!args || typeof args !== 'object' || Array.isArray(args) ||
          !Object.keys(args).every(k => ['mood', 'animation', 'speech', 'duration_seconds', 'priority'].includes(k))) {
        throw new Error('Invalid pet_action arguments');
      }
      return submitPetAction(args);
    },
  });
}
