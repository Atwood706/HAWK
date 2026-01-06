"""
AWDL Command Line Interface

This module provides the CLI for the AWDL compiler.
Commands: validate, compile, run
"""

import sys
import json
from pathlib import Path
from typing import Optional

import click

from awdl.language.parser import parse_file, parse_string
from awdl.language.errors import AWDLError
from awdl.compiler.langgraph import LangGraphCompiler


@click.group()
@click.version_option(version="0.1.0", prog_name="awdl")
def main():
    """
    AWDL - Agentic Workflow Description Language
    
    A domain-specific language for defining agent workflows.
    """
    pass


@main.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def validate(filepath: str, verbose: bool):
    """
    Parse and validate an AWDL workflow file.
    
    FILEPATH: Path to the .awdl file to validate
    """
    try:
        click.echo(f"Validating {filepath}...")
        
        # Parse the file
        workflow = parse_file(filepath)
        
        if verbose:
            click.echo(f"\nWorkflow: {workflow.name}")
            click.echo(f"Version: {workflow.version}")
            click.echo(f"Imports: {len(workflow.imports)}")
            click.echo(f"Variables: {len(workflow.variables)}")
            click.echo(f"Elements: {len(workflow.elements)}")
        
        # Validate the workflow
        errors = workflow.validate()
        
        if errors:
            click.echo("\nValidation errors:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)
        
        # Check for circular dependencies
        analyzer = workflow.get_dependency_analyzer()
        cycle = analyzer.detect_cycles()
        
        if cycle:
            click.echo(f"\nCircular dependency detected: {' -> '.join(cycle)}", err=True)
            sys.exit(1)
        
        if verbose:
            # Show execution order
            order = analyzer.get_execution_order()
            click.echo("\nExecution order:")
            for i, element in enumerate(order, 1):
                click.echo(f"  {i}. {element.element_id}")
        
        click.echo(click.style("\n✓ Validation successful!", fg="green"))
        
    except AWDLError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--target", "-t", default="langgraph", 
              type=click.Choice(["langgraph"]),
              help="Target framework to compile to")
@click.option("--output", "-o", type=click.Path(), 
              help="Output file path (default: <input>_compiled.py)")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def compile(filepath: str, target: str, output: Optional[str], verbose: bool):
    """
    Compile an AWDL workflow to executable Python code.
    
    FILEPATH: Path to the .awdl file to compile
    """
    try:
        click.echo(f"Compiling {filepath} to {target}...")
        
        # Parse the file
        workflow = parse_file(filepath)
        
        # Validate first
        errors = workflow.validate()
        if errors:
            click.echo("\nValidation errors:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)
        
        # Create compiler based on target
        if target == "langgraph":
            compiler = LangGraphCompiler(workflow)
        else:
            click.echo(f"Unknown target: {target}", err=True)
            sys.exit(1)
        
        # Validate compilation
        compile_errors = compiler.validate()
        if compile_errors:
            click.echo("\nCompilation errors:", err=True)
            for error in compile_errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)
        
        # Compile
        code = compiler.compile()
        
        # Determine output path
        if output is None:
            input_path = Path(filepath)
            output = str(input_path.with_suffix("")) + "_compiled.py"
        
        # Write output
        with open(output, "w") as f:
            f.write(code)
        
        click.echo(click.style(f"\n✓ Compiled successfully to {output}", fg="green"))
        
        if verbose:
            click.echo("\nGenerated code preview:")
            click.echo("-" * 40)
            # Show first 50 lines
            lines = code.split("\n")
            preview = "\n".join(lines[:50])
            click.echo(preview)
            if len(lines) > 50:
                click.echo(f"\n... ({len(lines) - 50} more lines)")
        
    except AWDLError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
@click.argument("filepath", type=click.Path(exists=True))
@click.option("--input", "-i", "input_json", type=str, 
              help="Input state as JSON (e.g., '{\"user_query\": \"Hello\"}')")
@click.option("--target", "-t", default="langgraph",
              type=click.Choice(["langgraph"]),
              help="Target framework to compile to")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
def run(filepath: str, input_json: Optional[str], target: str, verbose: bool):
    """
    Compile and run an AWDL workflow.
    
    FILEPATH: Path to the .awdl file to run
    """
    try:
        click.echo(f"Running {filepath}...")
        
        # Parse the file
        workflow = parse_file(filepath)
        
        # Validate
        errors = workflow.validate()
        if errors:
            click.echo("\nValidation errors:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)
        
        # Create compiler
        if target == "langgraph":
            compiler = LangGraphCompiler(workflow)
        else:
            click.echo(f"Unknown target: {target}", err=True)
            sys.exit(1)
        
        # Compile
        code = compiler.compile()
        
        if verbose:
            click.echo("\nCompiled workflow:")
            click.echo("-" * 40)
            click.echo(code[:500])
            if len(code) > 500:
                click.echo("...")
        
        # Parse input state
        input_state = {}
        if input_json:
            try:
                # 首先尝试作为 JSON 解析
                input_state = json.loads(input_json)
            except json.JSONDecodeError:
                # 如果失败，尝试作为 key=value 格式解析
                # 例如: user_query=Hello
                try:
                    input_state = {}
                    for pair in input_json.split(','):
                        key, value = pair.split('=', 1)
                        input_state[key.strip()] = value.strip()
                    click.echo(f"Parsed as key=value format: {input_state}")
                except Exception:
                    example = '{"key": "value"}'
                    click.echo(f"Invalid input format. Use JSON like '{example}' or key=value format", err=True)
                    sys.exit(1)
        
        # For now, we just show what would be executed
        # Actual execution would require the LangGraph runtime
        click.echo("\n" + "=" * 40)
        click.echo("Workflow compiled successfully!")
        click.echo("=" * 40)
        click.echo(f"\nWorkflow: {workflow.name}")
        click.echo(f"Elements: {len(workflow.elements)}")
        
        # Show execution order
        analyzer = workflow.get_dependency_analyzer()
        order = analyzer.get_execution_order()
        
        click.echo("\nExecution order:")
        for i, element in enumerate(order, 1):
            click.echo(f"  {i}. {element.element_id} ({type(element).__name__})")
        
        if input_state:
            click.echo(f"\nInput state: {json.dumps(input_state, indent=2)}")
        
        click.echo("\n" + click.style(
            "Note: To actually run the workflow, execute the generated Python file.",
            fg="yellow"
        ))
        
    except AWDLError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Unexpected error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@main.command()
def info():
    """
    Show information about AWDL.
    """
    click.echo("""
AWDL - Agentic Workflow Description Language
=============================================

AWDL is a domain-specific language for defining agent workflows in a simple,
declarative manner. It allows users to describe complex agent workflows without
dealing with the underlying framework implementation details.

Key Features:
  - Simple, readable syntax for defining workflows
  - Framework-agnostic intermediate representation
  - Variable-driven dependencies (no explicit edges)
  - Compilation to multiple target frameworks

Supported Targets:
  - LangGraph (primary)
  - More coming soon (Agno, etc.)

For more information, visit: https://github.com/hawk-team/awdl
    """)


if __name__ == "__main__":
    main()

