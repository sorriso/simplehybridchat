/* path: src/components/sidebar/NewConversationButton.tsx
   version: 1 */

import { Plus } from "lucide-react";
import { Button } from "../ui/Button";

interface NewConversationButtonProps {
  onClick: () => void;
}

/**
 * Button to create a new conversation
 */
export function NewConversationButton({ onClick }: NewConversationButtonProps) {
  return (
    <Button
      onClick={onClick}
      variant="primary"
      fullWidth
      className="flex items-center justify-center gap-2"
    >
      <Plus size={20} />
      <span>New Conversation</span>
    </Button>
  );
}
