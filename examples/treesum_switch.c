// Tree traversal; a recursive variation of `itersum.c`
// Now using `switch`!
#include <stdint.h>
#include <stdlib.h>
#include <stdbool.h>
#include <stdio.h>
#include <fiber_switch.h>

static int argc_global;
static char** argv_global;

static fiber_t runner;
static fiber_t walker;

static bool walk_done = false;

typedef struct node {
  enum { LEAF, FORK } tag;
  union {
    // Leaf.
    int32_t val;
    // Fork
    struct {
      struct node *left;
      struct node *right;
    };
  };
} node_t;

node_t* build_tree(int32_t depth, int32_t val) {
  node_t *node = (node_t*)malloc(sizeof(node_t));
  if (depth == 0) {
    node->tag = LEAF;
    node->val = val;
  } else {
    node->tag = FORK;
    node_t *subtree = build_tree(depth - 1, val + 1);
    node->left = subtree;
    node->right = subtree;
  }
  return node;
}

void free_tree(node_t *node) {
  enum { LEAF, FORK } tag = node->tag;
  if (tag == FORK) {
    if (node->left == node->right) {
      free_tree(node->left);
    } else {
      free_tree(node->left);
      free_tree(node->right);
    }
  }
  free(node);
}

void walk_tree(node_t *node) {
  if (node->tag == LEAF) {
    fiber_switch(runner, (void*)(intptr_t)node->val, &walker);
  } else {
    walk_tree(node->left);
    walk_tree(node->right);
  }
}

void* tree_walker(void *node, fiber_t  __attribute__((unused))main_fiber) {
  walk_tree((node_t*)node);
  walk_done = true;
  fiber_return_switch(runner, NULL);
  return NULL;
}

int32_t run(node_t* tree, fiber_t main_fiber) {
  int32_t sum = 0;
  walker = fiber_alloc((fiber_entry_point_t)tree_walker);
  void* val = fiber_switch(walker, (void*)tree, &runner);

  while (!walk_done) {
    sum += (int32_t)(intptr_t)val;
    val = fiber_switch(walker, NULL, &runner);
  }

  fiber_free(walker);
  fiber_return_switch(main_fiber, (void*)(intptr_t)sum);

  return 0;
}

void *prog(void * __attribute__((unused))unused_result, fiber_t dummy) {

  if (argc_global != 2) {
    fprintf(stderr, "Wrong number of arguments. Expected: 1");
    return 0;
  }

  int i = atoi(argv_global[1]);
  
  node_t *tree = build_tree((int32_t)i, 0);

  runner = fiber_alloc((fiber_entry_point_t)run);

  int32_t result = (int32_t)fiber_switch(runner, (void*)(intptr_t)tree, &dummy);

  fiber_free(runner);

  free_tree(tree);

  printf("%d\n", result);

  return 0;
}

int main(int argc, char** argv) {

  argc_global = argc;
  argv_global = argv;

  void *result = fiber_main(prog, NULL);
  
  return (int)(intptr_t)result;
}
