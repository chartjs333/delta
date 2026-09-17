export type PairwiseAnswer = "YES" | "NO" | "UNKNOWN" | "UNANSWERED";
export type PairwiseReviewState = "ACTIVE" | "STALE" | "ORPHANED";
export type PairwiseQuestion =
  | "sharedPrivateKey"
  | "sharedAdministrator"
  | "sharedRecoveryOrBackupAccess";

export interface ControllerDraftIdentity {
  readonly draftControllerKey: string;
  readonly controllerId?: string;
}

export interface PairwiseReviewDraft {
  readonly pairKey: string;
  readonly memberKeys: readonly [string, string];
  readonly controllerIdSnapshots: readonly [string | null, string | null];
  readonly answers: Readonly<Record<PairwiseQuestion, PairwiseAnswer>>;
  readonly evidenceReferences: readonly string[];
  readonly state: PairwiseReviewState;
}

export const pairwiseQuestions: readonly {
  readonly id: PairwiseQuestion;
  readonly label: string;
}[] = [
  { id: "sharedPrivateKey", label: "Do these controllers share a private key?" },
  { id: "sharedAdministrator", label: "Do these controllers share an administrator?" },
  {
    id: "sharedRecoveryOrBackupAccess",
    label: "Do these controllers share recovery or backup access?",
  },
];

function snapshot(identity: ControllerDraftIdentity): string | null {
  return identity.controllerId ?? null;
}

function orderedMemberKeys(
  first: string,
  second: string,
): readonly [string, string] {
  if (first === second) {
    throw new TypeError("A pair requires two distinct controller draft keys.");
  }
  return first < second ? [first, second] : [second, first];
}

export function pairKeyFor(first: string, second: string): string {
  const [left, right] = orderedMemberKeys(first, second);
  return `${left.length}:${left}|${right.length}:${right}`;
}

function createPairwiseReviewDraft(
  first: ControllerDraftIdentity,
  second: ControllerDraftIdentity,
): PairwiseReviewDraft {
  const members = orderedMemberKeys(
    first.draftControllerKey,
    second.draftControllerKey,
  );
  const identities = new Map([
    [first.draftControllerKey, first],
    [second.draftControllerKey, second],
  ]);
  return {
    pairKey: pairKeyFor(...members),
    memberKeys: members,
    controllerIdSnapshots: [
      snapshot(identities.get(members[0]) as ControllerDraftIdentity),
      snapshot(identities.get(members[1]) as ControllerDraftIdentity),
    ],
    answers: {
      sharedPrivateKey: "UNANSWERED",
      sharedAdministrator: "UNANSWERED",
      sharedRecoveryOrBackupAccess: "UNANSWERED",
    },
    evidenceReferences: [],
    state: "ACTIVE",
  };
}

function lifecycleState(
  record: PairwiseReviewDraft,
  currentByKey: ReadonlyMap<string, ControllerDraftIdentity>,
): PairwiseReviewState {
  const first = currentByKey.get(record.memberKeys[0]);
  const second = currentByKey.get(record.memberKeys[1]);
  if (!first || !second) {
    return "ORPHANED";
  }
  return snapshot(first) === record.controllerIdSnapshots[0] &&
    snapshot(second) === record.controllerIdSnapshots[1]
    ? "ACTIVE"
    : "STALE";
}

export function syncPairwiseReviewDrafts(
  controllers: readonly ControllerDraftIdentity[],
  previous: readonly PairwiseReviewDraft[],
): readonly PairwiseReviewDraft[] {
  const currentByKey = new Map(
    controllers.map((controller) => [controller.draftControllerKey, controller]),
  );
  const synchronized = previous.map((record) => ({
    ...record,
    state: lifecycleState(record, currentByKey),
  }));
  const knownPairKeys = new Set(synchronized.map((record) => record.pairKey));

  for (let first = 0; first < controllers.length; first += 1) {
    for (let second = first + 1; second < controllers.length; second += 1) {
      const pairKey = pairKeyFor(
        controllers[first].draftControllerKey,
        controllers[second].draftControllerKey,
      );
      if (!knownPairKeys.has(pairKey)) {
        synchronized.push(
          createPairwiseReviewDraft(controllers[first], controllers[second]),
        );
        knownPairKeys.add(pairKey);
      }
    }
  }
  return synchronized;
}

export function updatePairwiseAnswer(
  record: PairwiseReviewDraft,
  question: PairwiseQuestion,
  answer: Exclude<PairwiseAnswer, "UNANSWERED">,
): PairwiseReviewDraft {
  return {
    ...record,
    answers: { ...record.answers, [question]: answer },
  };
}

export function updatePairwiseEvidence(
  record: PairwiseReviewDraft,
  text: string,
): PairwiseReviewDraft {
  return {
    ...record,
    evidenceReferences: text
      .split(/\r?\n/u)
      .map((reference) => reference.trim())
      .filter(Boolean),
  };
}

export function acceptCurrentControllerIds(
  record: PairwiseReviewDraft,
  controllers: readonly ControllerDraftIdentity[],
): PairwiseReviewDraft {
  const currentByKey = new Map(
    controllers.map((controller) => [controller.draftControllerKey, controller]),
  );
  const first = currentByKey.get(record.memberKeys[0]);
  const second = currentByKey.get(record.memberKeys[1]);
  if (!first || !second) {
    return { ...record, state: "ORPHANED" };
  }
  return {
    ...record,
    controllerIdSnapshots: [snapshot(first), snapshot(second)],
    state: "ACTIVE",
  };
}

export function isPairwiseRecordFilled(record: PairwiseReviewDraft): boolean {
  return Object.values(record.answers).every(
    (answer) => answer !== "UNANSWERED",
  );
}
