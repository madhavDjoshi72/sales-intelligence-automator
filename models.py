"""
Pydantic schema for the structured sales brief.
The LLM is instructed to return JSON matching this exact shape.
Validating against this model is how we keep the LLM's output strict —
if it doesn't match, we retry with an error message instead of accepting junk.
"""

from pydantic import BaseModel, Field


class SalesBrief(BaseModel):
    company_name: str = Field(description="Best-guess name of the company")
    company_overview: str = Field(description="1-3 sentences on what the company does")
    core_product_or_service: str = Field(description="The main product/service they offer")
    target_customer: str = Field(description="Who their customers/audience are")
    is_b2b_lead: bool = Field(description="True if this looks like a relevant B2B lead")
    b2b_reasoning: str = Field(description="Short justification for the yes/no decision")
    sales_questions: list[str] = Field(
        description="Exactly 3 specific questions a sales rep should ask",
        min_length=3,
        max_length=3,
    )
    source_url: str | None = Field(default=None, description="URL that was scraped, if any")
    notes: str | None = Field(default=None, description="Any caveats, e.g. limited data found")
