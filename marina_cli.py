#!/usr/bin/env python3
from core import key_env_loader
key_env_loader.load_env_keys(verbose=True)


import argparse
import sys

from core import key_manager
key_manager.load_keys()


# --- Marina Subsystem Imports ---
from core import contextual_engine
from llm import llm_router
from core import voice_interface
import self_destruct  # assumed at root level

def main():
    parser = argparse.ArgumentParser(description='Marina Command Line Interface')
    subparsers = parser.add_subparsers(dest='command', help='Subsystems')

    # Contextual Engine
    parser_context = subparsers.add_parser('context', help='Run system context scan')
    parser_context.add_argument('--mode', choices=['complete', 'inferred', 'none'], default='inferred', help='Scan mode')
    parser_context.add_argument('--whitelist', nargs='*', default=["~/Documents", "~/Desktop"], help='Whitelist directories')
    parser_context.add_argument('--blacklist', nargs='*', default=["~/Downloads"], help='Blacklist directories')

    # LLM Router
    parser_llm = subparsers.add_parser('llm', help='Route a task to an LLM')
    parser_llm.add_argument('task', help='Description of the task')
    parser_llm.add_argument('--tokens', type=int, default=500, help='Estimated token usage')
    parser_llm.add_argument('--save', action='store_true', help='Save the LLM response to file')
    parser_llm.add_argument('--model', choices=['gpt', 'gemini', 'claude', 'deepseek'], help='Force use of a specific LLM')
    parser_llm.add_argument('--format', choices=['text', 'code', 'json', 'image'], default='text', help='Format to save response as')
    parser_llm.add_argument('--language', help='Programming language if saving code')
    parser_llm.add_argument('--outfile', help='Override output file name')

    # Voice Mode
    subparsers.add_parser('voice', help='Activate voice interface')

    # Self Destruct
    parser_sd = subparsers.add_parser('self-destruct', help='Initiate self destruct')
    parser_sd.add_argument('--mode', choices=['dry_run', 'soft_wipe', 'hard_purge', 'burn_trace', 'dark_exit'], default='dry_run')

    args = parser.parse_args()

    if args.command == 'context':
        print(f"[MARINA] Running context scan in {args.mode} mode...")
        data = contextual_engine.scan_file_tree(
            base_path="~/",
            mode=args.mode,
            whitelist=args.whitelist,
            blacklist=args.blacklist
        )
        contextual_engine.save_context(data)
        print("[MARINA] Context scan completed and saved.")
    
    elif args.command == 'llm':
        print(f"[MARINA] Routing task: '{args.task}' with estimated {args.tokens} tokens...")

        model, result = llm_router.route_task(
            args.task,
            args.tokens,
            run=True,
            force_model=args.model
        )

        print(f"[MARINA] Best LLM selected: {model}")
        from llm import llm_logo

        # After model is selected and before output is shown
        llm_logo.print_logo(model)

        if result:
            print(f"\n[{model.upper()} RESPONSE]\n{result}")

            if args.save:
                from llm import gemini_saver
                if args.format == "code":
                    gemini_saver.save_code(result, language=args.language or "python", base=args.outfile or "marina_code")
                elif args.format == "json":
                    try:
                        import json
                        json_data = json.loads(result)
                        gemini_saver.save_json(json_data, base=args.outfile or "marina_json")
                    except Exception:
                        print("[WARN] Response not valid JSON. Saving as text instead.")
                        gemini_saver.save_text(result, base=args.outfile or "marina_output")
                elif args.format == "text":
                    gemini_saver.save_text(result, base=args.outfile or "marina_output")
                elif args.format == "image":
                    print("[ERROR] Direct image generation not yet supported from plain text.")

    elif args.command == 'voice':
        print("[MARINA] Activating voice interface...")
        try:
            text = voice_interface.listen_and_transcribe()
            print(f"[VOICE INPUT] {text}")
        except Exception as e:
            print(f"[ERROR] Voice recognition failed: {e}")
    
    elif args.command == 'self-destruct':
        print(f"[MARINA] Initiating self-destruct in {args.mode} mode...")
        getattr(self_destruct, args.mode)()
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
