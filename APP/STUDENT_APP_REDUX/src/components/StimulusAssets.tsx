import type { StimulusAsset } from '../types'

/**
 * Renders the visual stimulus (chart/figure/table crop) attached to a question.
 * The backend serving route (/api/stimulus-assets/{id}) returns the crop image,
 * so every asset is renderable as an <img> regardless of stimulus_type — table
 * and chart assets carry structured_data too, but the cropped image is what the
 * student needs to read the question.
 */
export function StimulusAssets({ assets }: { assets?: StimulusAsset[] | null }) {
  if (!assets || assets.length === 0) return null

  return (
    <div className="space-y-3 mb-4">
      {assets.map((asset) => {
        const caption = asset.title
          ? `${asset.title}${asset.source_page_number ? ` (p. ${asset.source_page_number})` : ''}`
          : asset.source_page_number
            ? `Source page ${asset.source_page_number}`
            : null
        return (
          <figure key={asset.id} className="bg-gray-50 rounded-lg border border-gray-100 p-3">
            <img
              src={asset.url}
              alt={asset.title ?? `${asset.stimulus_type} stimulus`}
              loading="lazy"
              className="max-w-full h-auto rounded mx-auto"
            />
            {caption && (
              <figcaption className="mt-2 text-xs text-gray-400 text-center">{caption}</figcaption>
            )}
          </figure>
        )
      })}
    </div>
  )
}