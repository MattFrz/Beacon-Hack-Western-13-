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
  ['TURN_LEFT', 'Turn left.'],
  ['TURN_RIGHT', 'Turn right.'],
  ['FOUND_IT', 'Found it.'],
  // Walk sentences: "{name}" is the bound target's label.
  ['INTRO_CONT_AHEAD', '{name} is straight ahead,'],
  ['INTRO_CONT_SLEFT', '{name} is slightly to your left,'],
  ['INTRO_CONT_LEFT', '{name} is to your left,'],
  ['INTRO_CONT_SRIGHT', '{name} is slightly to your right,'],
  ['INTRO_CONT_RIGHT', '{name} is to your right,'],
  ['INTRO_AHEAD', '{name} is straight ahead.'],
  ['INTRO_SLEFT', '{name} is slightly to your left.'],
  ['INTRO_LEFT', '{name} is to your left.'],
  ['INTRO_SRIGHT', '{name} is slightly to your right.'],
  ['INTRO_RIGHT', '{name} is to your right.'],
  ['DIR_AHEAD', 'Straight ahead.'],
  ['DIR_SLEFT', 'Slightly to your left.'],
  ['DIR_LEFT', 'To your left.'],
  ['DIR_SRIGHT', 'Slightly to your right.'],
  ['DIR_RIGHT', 'To your right.'],
  ['WITHIN_REACH', "within arm's reach."],
  ['STEPS_1', 'about one step ahead.'],
  ['STEPS_2', 'about two steps ahead.'],
  ['STEPS_3', 'about three steps ahead.'],
  ['STEPS_4', 'about four steps ahead.'],
  ['STEPS_5', 'about five steps ahead.'],
  ['STEPS_FAR', 'more than five steps away.'],
  ['TURN_SLIGHT_LEFT', 'Turn a little to your left.'],
  ['TURN_SLIGHT_RIGHT', 'Turn a little to your right.'],
  ['TURN_AROUND', 'Turn around.'],
  ['NEXT_TO', "It's next to another object."], // the landmark's name is not in clip_ids
];

export const CLIP_NAMES = CLIPS.map(([name]) => name);

// guided's last spoken clip ids -> one display sentence, e.g. [28, 24, 2, 11] -> "Keys about one metre".
export function captionFromClips(ids, targetName) {
  const words = ids
    .map((id) => (CLIPS[id]?.[0] === 'OBJECT_NAME' ? targetName : CLIPS[id]?.[1]?.replace('{name}', targetName ?? 'It')))
    .filter(Boolean);
  const text = words.join(' ');
  return text ? text[0].toUpperCase() + text.slice(1) : null;
}
