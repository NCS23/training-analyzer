import { useState, useCallback } from 'react';
import { Button, FileUpload, useToast } from '@nordlig/components';
import { Trash2 } from 'lucide-react';
import { uploadExerciseImages, deleteExerciseImages } from '@/api/exercises';
import type { Exercise } from '@/api/exercises';

interface ExerciseImageUploadProps {
  exerciseId: number;
  existingUrls: string[] | null;
  isCustom: boolean;
  isEditing: boolean;
  onImagesUpdated: (updated: Exercise) => void;
}

function ImageGrid({ urls }: { urls: string[] }) {
  return (
    <div className="grid grid-cols-2 gap-4">
      {urls.map((url, idx) => (
        <div key={idx} className="space-y-1.5">
          <div className="rounded-[var(--radius-component-md)] overflow-hidden bg-[var(--color-bg-subtle)]">
            <img
              src={url}
              alt={`Ausführung — ${idx === 0 ? 'Startposition' : 'Endposition'}`}
              className="w-full h-auto object-cover"
              loading="lazy"
            />
          </div>
          <p className="text-xs text-[var(--color-text-muted)] text-center">
            {idx === 0 ? 'Startposition' : 'Endposition'}
          </p>
        </div>
      ))}
    </div>
  );
}

export function ExerciseImageUpload({
  exerciseId,
  existingUrls,
  isCustom,
  isEditing,
  onImagesUpdated,
}: ExerciseImageUploadProps) {
  const { toast } = useToast();
  const [uploading, setUploading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const hasImages = existingUrls && existingUrls.length > 0;

  const handleUpload = useCallback(
    async (files: File[]) => {
      if (files.length === 0) return;
      setUploading(true);
      try {
        const updated = await uploadExerciseImages(exerciseId, {
          start: files[0],
          end: files[1],
        });
        onImagesUpdated(updated);
        toast({ title: 'Bilder hochgeladen', variant: 'success' });
      } catch {
        toast({ title: 'Upload fehlgeschlagen', variant: 'error' });
      } finally {
        setUploading(false);
      }
    },
    [exerciseId, onImagesUpdated, toast],
  );

  const handleDelete = useCallback(async () => {
    setDeleting(true);
    try {
      await deleteExerciseImages(exerciseId);
      onImagesUpdated({ image_urls: null } as Exercise);
      toast({ title: 'Bilder gelöscht', variant: 'success' });
    } catch {
      toast({ title: 'Löschen fehlgeschlagen', variant: 'error' });
    } finally {
      setDeleting(false);
    }
  }, [exerciseId, onImagesUpdated, toast]);

  // View mode: show existing images
  if (!isEditing || !isCustom) {
    if (!hasImages) return null;
    return <ImageGrid urls={existingUrls} />;
  }

  // Edit mode: upload zone + existing images with delete
  return (
    <div className="space-y-4">
      {hasImages && (
        <div className="space-y-3">
          <ImageGrid urls={existingUrls} />
          <Button
            variant="ghost"
            size="sm"
            onClick={handleDelete}
            disabled={deleting}
            className="text-[var(--color-text-error)]"
          >
            <Trash2 className="w-3.5 h-3.5 mr-1.5" />
            {deleting ? 'Lösche…' : 'Bilder entfernen'}
          </Button>
        </div>
      )}

      <FileUpload
        label={hasImages ? 'Bilder ersetzen' : 'Bilder hochladen'}
        accept=".jpg,.jpeg,.png"
        multiple
        maxSize={5}
        onUpload={handleUpload}
        preview
        disabled={uploading}
        instructionText="Start- und Endposition hierher ziehen"
        subText="JPG oder PNG, max. 5 MB pro Bild"
      />
    </div>
  );
}
