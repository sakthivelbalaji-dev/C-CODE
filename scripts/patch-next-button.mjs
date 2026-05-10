/**
 * Legacy fallback: injects the workspace "Next" button into an *old* minified bundle
 * when React source was missing. Current development uses QuestionPage.jsx + `vite build`.
 *
 * Idempotent: skips when the bundle already includes a Next control or modern patterns.
 */
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(__dirname, "..");
const assetsDir = path.join(repoRoot, "backend", "dist", "assets");

const HAS_NEXT_MARKERS = [
  "title:`Go to the next syllabus question`", // old injected patch
  "Go to the next question in syllabus order", // QuestionPage Next button title (partial)
  "syllabus-next?student_id=", // advanceToSyllabusNextQuestion with student progression
];

const NEEDLE =
  ",children:`Submit`})]})]}),(0,F.jsxs)(`aside`,{ref:w,className:`scrollbar-workspace ${oe} lg:max-h-[calc(100dvh-5.25rem)] lg:overflow-y-auto lg:pr-1`,children:[";

const REPLACEMENT =
  ",children:`Submit`}),(0,F.jsx)(`button`,{type:`button`,disabled:!_?.id||s,title:`Go to the next syllabus question`,onClick:async()=>{if(!_?.id)return;let e=await ie(_.id);e.ok?o(`Moved to the next syllabus question.`):e.noNext?o(`You are on the last question in this syllabus.`):o(`Could not open the next question. Try again shortly.`)},className:`rounded-xl bg-amber-500 px-5 py-2.5 text-sm font-semibold text-slate-900 shadow-[0_0_20px_-4px_rgba(245,158,11,0.55)] transition hover:brightness-110 disabled:opacity-50`,children:`Next`})]})]}),(0,F.jsxs)(`aside`,{ref:w,className:`scrollbar-workspace ${oe} lg:max-h-[calc(100dvh-5.25rem)] lg:overflow-y-auto lg:pr-1`,children:[";

function alreadyHasNext(s) {
  return HAS_NEXT_MARKERS.some((m) => s.includes(m));
}

function main() {
  if (!fs.existsSync(assetsDir)) {
    console.warn(`patch-next-button: no ${assetsDir}; skip.`);
    process.exit(0);
  }
  const files = fs.readdirSync(assetsDir).filter((f) => /^index-.*\.js$/.test(f));
  if (files.length === 0) {
    console.warn("patch-next-button: no index-*.js in assets; skip.");
    process.exit(0);
  }
  let changed = 0;
  for (const name of files) {
    const fp = path.join(assetsDir, name);
    let s = fs.readFileSync(fp, "utf8");
    if (alreadyHasNext(s)) {
      console.log(`patch-next-button: ${name} already has Next — ok.`);
      continue;
    }
    if (!s.includes(NEEDLE)) {
      console.warn(
        `patch-next-button: ${name} has no injectable pattern (expected from current Vite build with Next in source) — skip.`,
      );
      continue;
    }
    s = s.replace(NEEDLE, REPLACEMENT);
    fs.writeFileSync(fp, s, "utf8");
    console.log(`patch-next-button: updated ${name}`);
    changed++;
  }
  if (changed === 0 && files.length) {
    console.log("patch-next-button: done.");
  }
}

main();
