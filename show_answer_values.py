#!/usr/bin/env python3
"""Display answer value mappings for all questions."""

import json

# Load the admin question bank
with open('questiondb/psychometric_question_bank_v2_admin.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 80)
print("ANSWER VALUE MAPPING FOR ALL QUESTIONS")
print("=" * 80)
print("\nNote: Values range from 0-3")
print("  - 0 = weakest/highest risk behavior")
print("  - 1 = low/moderate risk")
print("  - 2 = moderate/good behavior")
print("  - 3 = strongest/most protective behavior")
print("\n" + "=" * 80)

for trait in data['traits']:
    trait_name = trait['trait_name']
    trait_id = trait['trait_id']
    
    print(f"\n{trait_id}. {trait_name}")
    print("-" * 80)
    
    for item in trait['items']:
        item_id = item['item_id']
        prompt = item['prompt']
        score_map = item['score_map_0_to_3']
        
        print(f"\n  Question {item_id}: {prompt}")
        print(f"  Answer Values:")
        
        # Sort by value (highest to lowest)
        sorted_scores = sorted(score_map.items(), key=lambda x: x[1], reverse=True)
        for option, value in sorted_scores:
            option_text = item['options'][option]
            print(f"    {option} = {value}  ({option_text})")

print("\n" + "=" * 80)
print("Summary: Each question has 4 options (A, B, C, D) mapped to values 0-3")
print("=" * 80)






