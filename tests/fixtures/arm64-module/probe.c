#include <linux/init.h>
#include <linux/module.h>
static int __init probe_start(void) { pr_info("PSYCACHY_MODULE_LOADED\n"); return 0; }
static void __exit probe_end(void) { }
module_init(probe_start);
module_exit(probe_end);
MODULE_LICENSE("GPL");

MODULE_DESCRIPTION("PsyCachy VM test module");
