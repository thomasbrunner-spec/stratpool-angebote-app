/**
 * TypeScript mirror of backend/app/routes/prompts.py — keep in sync.
 */

export interface GeneratePromptInfo {
  model: string;
  max_tokens: number;
  system: string;
  skeleton: string;
  user_message_example: string;
  user_message_notes: string;
}

export interface RenderPromptInfo {
  model: string;
  max_tokens: number;
  betas: string[];
  skills: Record<string, string>;
  pptx_user_message_example: string;
  word_user_message_example: string;
  user_message_notes: string;
}

export interface PromptsResponse {
  generate: GeneratePromptInfo;
  render: RenderPromptInfo;
}
