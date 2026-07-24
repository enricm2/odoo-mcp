from . import models, controllers


def uninstall_hook(cr_or_env, registry=None):
    """
    Clean up all ir.config.parameter entries created by this module.
    Odoo 16 calls uninstall_hook(cr, registry).
    Odoo 17+ calls uninstall_hook(env).
    """
    if registry is not None:
        # Odoo 16: first arg is the database cursor
        cr_or_env.execute(
            "DELETE FROM ir_config_parameter "
            "WHERE key LIKE 'ia_agents_treasury_control.%%'"
        )
    else:
        # Odoo 17+: first arg is env
        cr_or_env["ir.config_parameter"].sudo().search(
            [("key", "like", "ia_agents_treasury_control.")]
        ).unlink()
