// augment_kb.js
//
// Hand-authored editorial metadata layered on top of the pipeline-derived
// demo/gen/CLASSES_kb.js. This is a one-time content-authoring step (like
// legal_content.py already is) -- not something the ETL pipeline computes,
// because none of the fields added here have a source in the ticket data:
//
//   - legalStatements: turns the single legalStatement string into a
//     structured, verdict-carrying array (the shape the editor UI needs to
//     show a "Law" chip you can actually confirm/re-confirm, not just read).
//   - generalizationConfirmed: initial reviewed-state flag.
//   - history: a single honest baseline entry -- these 29 categories were
//     authored once and have no real prior edits, so the history does NOT
//     claim otherwise. Real entries get appended by the demo itself when a
//     change is published in-session.
//   - sharedBlockId: 3 categories (check_cancellation_fee, cancel_order,
//     check_refund_policy) already restate the same EU 14-day withdrawal
//     right in their own words -- genuinely duplicated content, not a
//     fabricated example -- so it's extracted into one shared block that
//     all three reference.
//
// Run with: node demo/content/augment_kb.js
// Reads + overwrites demo/gen/CLASSES_kb.js in place.

const fs = require('fs');
const path = require('path');

const OUT_PATH = path.join(__dirname, '..', 'gen', 'CLASSES_kb.js');
const src = fs.readFileSync(OUT_PATH, 'utf8');

// The file is `const CLASSES = [ ... ];` -- eval it in an isolated function
// scope to get the real array back (trusted, locally-generated content).
const CLASSES = (function () {
  const module = { exports: {} };
  const fn = new Function('module', 'exports', src + '\nmodule.exports = CLASSES;');
  fn(module, module.exports);
  return module.exports;
})();

const SHARED_BLOCK_ID = 'eu_withdrawal_right';
const SHARED_BLOCK_CATEGORY_IDS = ['check_cancellation_fee', 'cancel_order', 'check_refund_policy'];
const SHARED_BLOCK_TEXT =
  "EU consumers have a 14-day right of withdrawal under Directive 2011/83/EU, Articles 9-16: " +
  "they may cancel or return most items within 14 days of delivery, for a full refund, without " +
  "justification, bearing only the disclosed cost of return shipping (if OrbitDesk disclosed that " +
  "cost before purchase). Excluded under Article 16: custom/personalised goods, perishables, and " +
  "unsealed hygiene items.";

let augmented = 0;
let sharedApplied = 0;

CLASSES.forEach((cls) => {
  cls.items.forEach((it) => {
    it.generalizationConfirmed = true;
    it.legalStatements = [
      {
        statement: it.legalStatement,
        verdict: it.sourceType === 'external' ? 'confirmed' : 'internal',
      },
    ];
    it.history = [
      {
        who: 'Knowledge base import',
        when: 'initial export',
        note:
          "Initial published version -- from the pipeline export + hand-written knowledge-base " +
          "content. Not an edit made in this demo; there is no earlier version to show a diff against.",
      },
    ];
    augmented++;
    if (SHARED_BLOCK_CATEGORY_IDS.includes(it.id)) {
      it.sharedBlockId = SHARED_BLOCK_ID;
      sharedApplied++;
    }
  });
});

const SHARED_BLOCKS = {
  [SHARED_BLOCK_ID]: {
    text: SHARED_BLOCK_TEXT,
    usedIn: SHARED_BLOCK_CATEGORY_IDS,
  },
};

const out =
  `const CLASSES = ${JSON.stringify(CLASSES, null, 2)};\n\n` +
  `const SHARED_BLOCKS = ${JSON.stringify(SHARED_BLOCKS, null, 2)};\n`;

fs.writeFileSync(OUT_PATH, out, 'utf8');
console.log(`Augmented ${augmented} categories, applied sharedBlockId to ${sharedApplied}.`);
console.log('Wrote', OUT_PATH);
