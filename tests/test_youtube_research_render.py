from __future__ import annotations

import unittest

import youtube_research as yr


def legacy_render_markdown(data):
    lines = []

    lines.append(
        f"# {data['channel']} Research Brief"
    )

    lines.append(
        f"\nGenerated: {data['generated_at']}"
    )

    lines.append(
        f"\nModel: `{data['model']}`"
    )

    lines.append(
        f"\nTranscripts analyzed: "
        f"{len(data['source_videos'])}"
    )

    summary = data["summary"]
    extraction = data["extraction"]
    research = data["research"]

    lines.append(
        "\n## Channel Overview\n"
    )

    lines.append(
        summary.get(
            "channel_overview",
            ""
        )
    )

    lines.append(
        "\n## Detailed Summary\n"
    )

    lines.append(
        summary.get(
            "detailed_summary",
            ""
        )
    )

    lines.append(
        "\n## Key Themes\n"
    )

    for item in summary.get(
        "key_themes",
        []
    ):
        if isinstance(item, dict):
            lines.append(
                f"- **{item.get('theme', '')}** — "
                f"{item.get('explanation', '')}"
            )
        else:
            lines.append(
                f"- {item}"
            )

    lines.append(
        "\n## Keywords\n"
    )

    for item in extraction.get(
        "keywords",
        []
    ):
        lines.append(
            f"- {item}"
        )

    lines.append(
        "\n## Tags\n"
    )

    tags = extraction.get(
        "tags",
        []
    )

    lines.append(
        " ".join(
            tag
            if str(tag).startswith("#")
            else "#" + str(tag).replace(
                " ",
                "-"
            )
            for tag in tags
        )
    )

    lines.append(
        "\n## Resources Mentioned\n"
    )

    resources = extraction.get(
        "resources",
        []
    )

    if not resources:
        lines.append(
            "No explicit resources extracted."
        )

    for item in resources:
        if not isinstance(
            item,
            dict
        ):
            lines.append(
                f"- {item}"
            )
            continue

        lines.append(
            f"\n### {item.get('name', 'Unnamed resource')}"
        )

        lines.append(
            f"- **Type:** {item.get('type', '')}"
        )

        lines.append(
            f"- **Why mentioned:** "
            f"{item.get('why_mentioned', '')}"
        )

        url = item.get(
            "url",
            ""
        )

        lines.append(
            f"- **URL:** "
            f"{url if url else 'not supplied'}"
        )

        lines.append(
            f"- **Search term:** "
            f"{item.get('search_term', '')}"
        )

    lines.append(
        "\n## People\n"
    )

    for item in extraction.get(
        "people",
        []
    ):
        if isinstance(item, dict):
            lines.append(
                f"- **{item.get('name', '')}** — "
                f"{item.get('context', '')}"
            )
        else:
            lines.append(
                f"- {item}"
            )

    lines.append(
        "\n## Organizations\n"
    )

    for item in extraction.get(
        "organizations",
        []
    ):
        if isinstance(item, dict):
            lines.append(
                f"- **{item.get('name', '')}** — "
                f"{item.get('context', '')}"
            )
        else:
            lines.append(
                f"- {item}"
            )

    category_sections = [
        (
            "Books",
            "books"
        ),
        (
            "Websites",
            "websites"
        ),
        (
            "Tools",
            "tools"
        ),
        (
            "Medical Terms",
            "medical_terms"
        ),
        (
            "Legal Terms",
            "legal_terms"
        ),
        (
            "Psychology Terms",
            "psychology_terms"
        ),
        (
            "Technologies",
            "technologies"
        ),
    ]

    for title, key in category_sections:
        values = extraction.get(
            key,
            []
        )

        if not values:
            continue

        lines.append(
            f"\n## {title}\n"
        )

        for item in values:
            lines.append(
                f"- {item}"
            )

    lines.append(
        "\n## Things To Look Up\n"
    )

    for item in research.get(
        "research_queries",
        []
    ):
        lines.append(
            f"- `{item}`"
        )

    lines.append(
        "\n## Notable Claims\n"
    )

    for item in research.get(
        "notable_claims",
        []
    ):
        if isinstance(item, dict):
            lines.append(
                f"- **Claim:** "
                f"{item.get('claim', '')}"
            )

            if item.get(
                "context"
            ):
                lines.append(
                    f"  - Context: "
                    f"{item.get('context')}"
                )

            if item.get(
                "verification_needed"
            ):
                lines.append(
                    "  - Verification: independent verification recommended"
                )
        else:
            lines.append(
                f"- {item}"
            )

    lines.append(
        "\n## Practical Takeaways\n"
    )

    for item in summary.get(
        "practical_takeaways",
        []
    ):
        lines.append(
            f"- {item}"
        )

    lines.append(
        "\n## Questions Raised\n"
    )

    for item in research.get(
        "questions_raised",
        []
    ):
        lines.append(
            f"- {item}"
        )

    lines.append(
        "\n## Topics To Verify\n"
    )

    for item in research.get(
        "topics_to_verify",
        []
    ):
        lines.append(
            f"- {item}"
        )

    lines.append(
        "\n## Concept Connections\n"
    )

    for item in research.get(
        "connections",
        []
    ):
        if isinstance(item, dict):
            lines.append(
                f"- **{item.get('concept_a', '')} ↔ "
                f"{item.get('concept_b', '')}** — "
                f"{item.get('relationship', '')}"
            )

    lines.append(
        "\n## Source Videos\n"
    )

    for video in data[
        "source_videos"
    ]:
        lines.append(
            f"\n### {video['title']}"
        )

        lines.append(
            f"- Video ID: `{video['video_id']}`"
        )

        lines.append(
            f"- Upload date: "
            f"{video['upload_date'] or 'unknown'}"
        )

        lines.append(
            f"- URL: "
            f"{video['url'] or 'not supplied'}"
        )

    return "\n".join(lines) + "\n"


FULL_DATA = {
    "channel": "Richmack Test Channel",
    "generated_at": "2026-08-14T17:00:00-04:00",
    "model": "gemma3:4b",
    "source_videos": [
        {
            "title": "AI, Linux and the Future",
            "video_id": "abc123",
            "upload_date": "20260810",
            "url": "https://example.test/abc123",
        },
        {
            "title": "Health Research Discussion",
            "video_id": "def456",
            "upload_date": "",
            "url": "",
        },
    ],
    "summary": {
        "channel_overview": "A technology and research channel.",
        "detailed_summary": "Detailed research summary.",
        "key_themes": [
            {
                "theme": "Artificial Intelligence",
                "explanation": "AI systems and development.",
            },
            "Linux administration",
        ],
        "practical_takeaways": [
            "Test claims independently.",
            "Keep source evidence.",
        ],
    },
    "extraction": {
        "keywords": [
            "artificial intelligence",
            "linux",
        ],
        "tags": [
            "AI",
            "#Linux",
            "Machine Learning",
        ],
        "resources": [
            {
                "name": "Example Tool",
                "type": "software",
                "why_mentioned": "Used for testing.",
                "url": "https://example.test/tool",
                "search_term": "example tool",
            },
            "Plain resource",
        ],
        "people": [
            {
                "name": "Ada Lovelace",
                "context": "Historical computing reference.",
            },
            "Anonymous researcher",
        ],
        "organizations": [
            {
                "name": "Example Labs",
                "context": "Research organization.",
            },
            "Open group",
        ],
        "books": [
            "Example Book",
        ],
        "websites": [
            "example.test",
        ],
        "tools": [
            "Linux",
        ],
        "medical_terms": [
            "growth hormone",
        ],
        "legal_terms": [
            "evidence",
        ],
        "psychology_terms": [
            "cognition",
        ],
        "technologies": [
            "Docker",
        ],
    },
    "research": {
        "research_queries": [
            "AI model efficiency",
            "Linux container security",
        ],
        "notable_claims": [
            {
                "claim": "Models are becoming more efficient.",
                "context": "Discussed during the interview.",
                "verification_needed": True,
            },
            {
                "claim": "Linux usage is growing.",
                "context": "",
                "verification_needed": False,
            },
            "Unstructured claim",
        ],
        "questions_raised": [
            "How should AI efficiency be measured?",
        ],
        "topics_to_verify": [
            "Model benchmark claims",
        ],
        "connections": [
            {
                "concept_a": "AI",
                "concept_b": "Linux",
                "relationship": "AI workloads often run on Linux.",
            },
            "ignored non-dict connection",
        ],
    },
}


EMPTY_DATA = {
    "channel": "Empty Channel",
    "generated_at": "2026-08-14",
    "model": "test-model",
    "source_videos": [],
    "summary": {},
    "extraction": {},
    "research": {},
}


class ResearchMarkdownCharacterizationTests(
    unittest.TestCase
):

    def test_full_document_matches_legacy(self):
        self.assertEqual(
            yr.render_markdown(
                FULL_DATA
            ),
            legacy_render_markdown(
                FULL_DATA
            ),
        )

    def test_empty_document_matches_legacy(self):
        self.assertEqual(
            yr.render_markdown(
                EMPTY_DATA
            ),
            legacy_render_markdown(
                EMPTY_DATA
            ),
        )

    def test_output_ends_with_newline(self):
        result = yr.render_markdown(
            FULL_DATA
        )

        self.assertTrue(
            result.endswith("\n")
        )

    def test_resource_fallbacks_preserved(self):
        data = {
            **EMPTY_DATA,
            "extraction": {
                "resources": [
                    {
                        "name": "No URL Resource",
                    }
                ]
            },
        }

        result = yr.render_markdown(
            data
        )

        self.assertIn(
            "not supplied",
            result,
        )


if __name__ == "__main__":
    unittest.main()
