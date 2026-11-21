// What each guided clip id says, in the order of `enum beacon_clip` in include/beacon.h.
// clips.test.js fails when that enum changes, so update both together.
const CLIPS = [
  ['NONE', ''],
  ['NUM_0', 'zero'], ['NUM_1', 'one'], ['NUM_2', 'two'], ['NUM_3', 'three'], ['NUM_4', 'four'],
  ['NUM_5', 'five'], ['NUM_6', 'six'], ['NUM_7', 'seven'], ['NUM_8', 'eight'], ['NUM_9', 'nine'],
  ['METRE', 'metre'],
  ['METRES', 'metres'],
  ['AHEAD', 'ahead'],
  ['LEFT', 'left'],
  ['RIGHT', 'right'],
  ['UP', 'up'],
  ['DOWN', 'down'],
  ['LOST_TARGET', 'I lost the target.'],
  ['STOPPING', 'Stopping.'],
  ['NOT_SEEN', 'I have not seen that.'],
  ['CANNOT_RETRACE', 'I cannot retrace without a path.'],
  ['DID_NOT_CATCH', 'I did not catch that.'],
  ['CANNOT_HELP', 'I cannot help with that.'],
  ['ABOUT', 'about'],
  ['A_LITTLE', 'a little'],
  ['YOU_ARE_BACK', 'You are back.'],
  ['PROMPT_BEEP', ''],
  ['OBJECT_NAME', null], // the bound target's label
];

export const CLIP_NAMES = CLIPS.map(([name]) => name);

// guided's last spoken clip ids -> one display sentence, e.g. [28, 24, 2, 11] -> "Keys about one metre".
export function captionFromClips(ids, targetName) {
  const words = ids.map((id) => (CLIPS[id]?.[0] === 'OBJECT_NAME' ? targetName : CLIPS[id]?.[1])).filter(Boolean);
  const text = words.join(' ');
  return text ? text[0].toUpperCase() + text.slice(1) : null;
}
