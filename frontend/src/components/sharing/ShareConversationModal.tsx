/* path: frontend/src/components/sharing/ShareConversationModal.tsx
   version: 2 - FIXED: Removed isOpen prop and renamed availableGroups to userGroups for compatibility with page.tsx */

import { useState } from "react";
import { Share2, X } from "lucide-react";
import { Modal } from "../ui/Modal";
import { Button } from "../ui/Button";
import type { UserGroup } from "@/types/auth";
import type { Conversation } from "@/types/conversation";

interface ShareConversationModalProps {
  onClose: () => void;
  conversation: Conversation;
  userGroups: UserGroup[];
  onShare: (groupIds: string[]) => Promise<void>;
  onUnshare: (groupIds: string[]) => Promise<void>;
}

/**
 * Modal to manage conversation sharing with user groups
 */
export function ShareConversationModal({
  onClose,
  conversation,
  userGroups,
  onShare,
  onUnshare,
}: ShareConversationModalProps) {
  const [selectedGroupIds, setSelectedGroupIds] = useState<Set<string>>(
    new Set(conversation.sharedWithGroupIds || []),
  );
  const [saving, setSaving] = useState(false);

  const toggleGroup = (groupId: string) => {
    const newSelection = new Set(selectedGroupIds);
    if (newSelection.has(groupId)) {
      newSelection.delete(groupId);
    } else {
      newSelection.add(groupId);
    }
    setSelectedGroupIds(newSelection);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const currentShared = new Set(conversation.sharedWithGroupIds || []);
      const toShare = Array.from(selectedGroupIds).filter(
        (id) => !currentShared.has(id),
      );
      const toUnshare = Array.from(currentShared).filter(
        (id) => !selectedGroupIds.has(id),
      );

      if (toShare.length > 0) {
        await onShare(toShare);
      }
      if (toUnshare.length > 0) {
        await onUnshare(toUnshare);
      }

      onClose();
    } catch (error) {
      console.error("Error saving share settings:", error);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose} title="Share Conversation" size="md">
      <div className="space-y-4">
        {/* Info */}
        <p className="text-sm text-gray-600">
          Select user groups to share this conversation with. Members of
          selected groups will be able to view this conversation.
        </p>

        {/* Conversation info */}
        <div className="p-3 bg-gray-50 rounded-lg">
          <p className="text-sm font-medium text-gray-900">
            {conversation.title}
          </p>
          <p className="text-xs text-gray-500 mt-1">
            {conversation.messageCount} messages
          </p>
        </div>

        {/* Group selection */}
        <div className="space-y-2">
          <label className="block text-sm font-medium text-gray-700">
            User Groups
          </label>

          {userGroups.length === 0 ? (
            <p className="text-sm text-gray-500 italic">
              No user groups available
            </p>
          ) : (
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {userGroups.map((group) => (
                <label
                  key={group.id}
                  className="flex items-center p-3 border border-gray-200 rounded-lg hover:bg-gray-50 cursor-pointer"
                >
                  <input
                    type="checkbox"
                    checked={selectedGroupIds.has(group.id)}
                    onChange={() => toggleGroup(group.id)}
                    className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                  />
                  <div className="ml-3 flex-1">
                    <p className="text-sm font-medium text-gray-900">
                      {group.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {group.memberIds.length} member(s) • {group.status}
                    </p>
                  </div>
                </label>
              ))}
            </div>
          )}
        </div>

        {/* Actions */}
        <div className="flex gap-2 justify-end pt-4 border-t">
          <Button variant="secondary" onClick={onClose} disabled={saving}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={handleSave}
            disabled={saving || userGroups.length === 0}
            className="flex items-center gap-2"
          >
            <Share2 size={16} />
            {saving ? "Saving..." : "Save Changes"}
          </Button>
        </div>
      </div>
    </Modal>
  );
}
